/**
 * [PRO-B-30] 세션 및 ReEntryLatency 관리.
 * - app_open 시 app_open_at 기록
 * - 첫 액션 시 first_action_at 기록, ReEntryLatency(ms) 계산 저장
 * - 첫 액션 없이 종료 시 first_action_at = null 유지
 */
const { v4: uuidv4 } = require('uuid');
const config = require('../../config');
const sessionLogRepo = require('../repositories/sessionLogRepository');
const { logSessionEvent } = require('../../logger');

const ACTION_TYPES = Object.freeze({
  GOAL_CREATE: 'goal_create',
  CHECK: 'check',
  OTHER: 'other',
});

/**
 * 앱 진입 이벤트 수신 시 세션 시작 시각(app_open_at) 기록.
 * Returns: { session_id, user_id, app_open_at }
 */
async function startSession(userId) {
  const sessionId = uuidv4();
  const appOpenAt = new Date();

  await sessionLogRepo.create({
    session_id: sessionId,
    user_id: userId,
    app_open_at: appOpenAt,
    action_type: null,
  });

  logSessionEvent('app_open', {
    session_id: sessionId,
    user_id: userId,
    app_open_at: appOpenAt,
    reentry_latency_ms: null,
    action_type: null,
    session_ended: false,
  });

  return { session_id: sessionId, user_id: userId, app_open_at: appOpenAt };
}

/**
 * 첫 액션(목표 생성/체크) 발생 시 first_action_at 기록 및 ReEntryLatency(ms) 계산 저장.
 * 이미 first_action_at이 있으면 last_action_at만 갱신.
 * actionType: 'goal_create' | 'check' | 'other'
 */
async function recordFirstOrLastAction(sessionId, actionType = ACTION_TYPES.OTHER) {
  const session = await sessionLogRepo.findBySessionId(sessionId);
  if (!session) return null;

  const now = new Date();
  const isFirst = session.first_action_at == null;

  if (isFirst) {
    const appOpenAt = new Date(session.app_open_at);
    const reentryLatencyMs = Math.max(0, now.getTime() - appOpenAt.getTime());

    await sessionLogRepo.updateFirstAction(
      sessionId,
      now,
      reentryLatencyMs,
      actionType
    );

    logSessionEvent('first_action', {
      session_id: sessionId,
      user_id: session.user_id,
      app_open_at: session.app_open_at,
      first_action_at: now,
      reentry_latency_ms: reentryLatencyMs,
      action_type: actionType,
      session_ended: false,
    });

    return {
      session_id: sessionId,
      first_action_at: now,
      reentry_latency_ms: reentryLatencyMs,
      action_type: actionType,
      is_first_action: true,
    };
  }

  await sessionLogRepo.updateLastAction(sessionId, now, actionType);
  return {
    session_id: sessionId,
    last_action_at: now,
    action_type: actionType,
    is_first_action: false,
  };
}

/**
 * [PRO-B-27] TaskDisplayScope 적용: 당일 생성 데이터만 조회 시 사용하는 날짜 반환.
 */
function getScopeDate() {
  const today = new Date();
  return today.toISOString().slice(0, 10);
}

/**
 * 당일(또는 scope에 따른 날짜) 세션 목록 조회.
 */
async function getSessionsForUserInScope(userId) {
  const date = config.taskDisplayScope === 'today' ? getScopeDate() : getScopeDate();
  return sessionLogRepo.findSessionsByUserAndDate(userId, date);
}

module.exports = {
  ACTION_TYPES,
  startSession,
  recordFirstOrLastAction,
  getScopeDate,
  getSessionsForUserInScope,
};
