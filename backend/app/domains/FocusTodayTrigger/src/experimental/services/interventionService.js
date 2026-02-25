/**
 * [PRO-B-31] 무행동 감지 및 실험군 개입 트리거.
 * - InactionTriggerSeconds(기본 30초) 초과 무행동 감지
 * - 실험군(Experimental)에게만 개입 트리거 이벤트 발행 및 intervention_log 기록
 * - 인터랙션 클릭 후 목표 입력창 포커싱을 위한 상태값 반환 API
 */
const { v4: uuidv4 } = require('uuid');
const config = require('../../config');
const sessionLogRepo = require('../repositories/sessionLogRepository');
const interventionLogRepo = require('../repositories/interventionLogRepository');
const { getExperimentGroup, isExperimental } = require('../experimentGroup');
const { logInterventionEvent } = require('../../logger');

const INACTION_TRIGGER_MS = (config.inactionTriggerSeconds || 30) * 1000;

/**
 * 세션 기준 무행동 경과 시간(ms). first_action_at 없으면 app_open_at ~ now.
 */
function getInactionElapsedMs(session) {
  if (!session) return null;
  const from = session.first_action_at ? new Date(session.last_action_at || session.first_action_at) : new Date(session.app_open_at);
  return Date.now() - from.getTime();
}

/**
 * InactionTriggerSeconds 초과 여부 판단.
 */
function shouldTriggerInaction(session) {
  const elapsed = getInactionElapsedMs(session);
  if (elapsed == null) return false;
  return elapsed >= INACTION_TRIGGER_MS;
}

/**
 * 무행동 초과 감지 시 실험군이면 개입 트리거 발행 및 intervention_log 기록.
 * Returns: { triggered: boolean, experiment_group, log_id?, focus_input: boolean }
 */
async function checkAndTriggerIntervention(userId, sessionId) {
  const session = await sessionLogRepo.findBySessionId(sessionId);
  if (!session) return { triggered: false, experiment_group: null, focus_input: false };

  const experimentGroup = getExperimentGroup(userId);
  const overThreshold = shouldTriggerInaction(session);

  if (!overThreshold) {
    return { triggered: false, experiment_group: experimentGroup, focus_input: false };
  }

  // 이미 이 세션에서 개입 트리거된 적 있는지 (재발행 방지)
  const existing = await interventionLogRepo.findLatestBySession(sessionId);
  if (existing) {
    return {
      triggered: false,
      experiment_group: experimentGroup,
      log_id: existing.log_id,
      focus_input: true,
    };
  }

  // 실험군에만 개입 트리거 발행
  if (!isExperimental(userId)) {
    return { triggered: false, experiment_group: experimentGroup, focus_input: false };
  }

  const triggeredAt = new Date();
  const logId = uuidv4();

  await interventionLogRepo.create({
    log_id: logId,
    user_id: userId,
    session_id: sessionId,
    experiment_group: experimentGroup,
    triggered_at: triggeredAt,
  });

  logInterventionEvent('triggered', {
    user_id: userId,
    session_id: sessionId,
    experiment_group: experimentGroup,
    triggered_at: triggeredAt,
    log_id: logId,
    first_action_after_trigger_at: null,
  });

  return {
    triggered: true,
    experiment_group: experimentGroup,
    log_id: logId,
    focus_input: true,
  };
}

/**
 * 인터랙션 클릭 후 첫 목표 입력창 포커싱을 위한 상태값 반환.
 * 클라이언트는 focus_input === true 일 때 입력창 포커스.
 */
async function getInterventionState(userId, sessionId) {
  const result = await checkAndTriggerIntervention(userId, sessionId);
  return {
    focus_input: result.focus_input,
    experiment_group: result.experiment_group,
    triggered: result.triggered,
    log_id: result.log_id ?? null,
  };
}

/**
 * 개입 트리거 이후 첫 액션 발생 시 first_action_after_trigger_at 갱신.
 */
async function recordFirstActionAfterTrigger(sessionId, firstActionAt) {
  const log = await interventionLogRepo.findLatestBySession(sessionId);
  if (!log || log.first_action_after_trigger_at) return null;

  await interventionLogRepo.updateFirstActionAfterTrigger(log.log_id, firstActionAt);

  logInterventionEvent('first_action_after_trigger', {
    user_id: log.user_id,
    session_id: sessionId,
    experiment_group: log.experiment_group,
    triggered_at: log.triggered_at,
    first_action_after_trigger_at: firstActionAt,
    log_id: log.log_id,
  });

  return { log_id: log.log_id, first_action_after_trigger_at: firstActionAt };
}

module.exports = {
  getInactionElapsedMs,
  shouldTriggerInaction,
  checkAndTriggerIntervention,
  getInterventionState,
  recordFirstActionAfterTrigger,
  INACTION_TRIGGER_MS,
};
