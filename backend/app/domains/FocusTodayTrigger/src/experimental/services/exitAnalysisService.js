/**
 * [PRO-B-32] 이탈 분석.
 * - app_close 시 pre_exit_inaction_ms = app_close_at - last_action_at
 * - 진입 후 60초 이내 종료 → 조기 이탈
 * - 무행동 구간이 기준치 이상 → is_high_risk_exit = true
 */
const config = require('../../config');
const sessionLogRepo = require('../repositories/sessionLogRepository');
const { logSessionEvent } = require('../../logger');

const EARLY_EXIT_THRESHOLD_MS = (config.earlyExitThresholdSeconds || 60) * 1000;
const HIGH_RISK_INACTION_MS = config.highRiskExitInactionMs || 30000;

/**
 * app_close 이벤트 수신 시 세션 종료 처리:
 * - app_close_at 기록
 * - pre_exit_inaction_ms = app_close_at - last_action_at (last_action_at 없으면 app_open_at 기준)
 * - 조기 이탈: app_close_at - app_open_at <= 60s
 * - is_high_risk_exit: pre_exit_inaction_ms >= 기준값 (또는 첫 액션 없이 종료)
 */
async function closeSession(sessionId, appCloseAt) {
  const session = await sessionLogRepo.findBySessionId(sessionId);
  if (!session) return null;

  const closeTime = appCloseAt ? new Date(appCloseAt) : new Date();
  const lastAt = session.last_action_at
    ? new Date(session.last_action_at)
    : new Date(session.app_open_at);
  const openAt = new Date(session.app_open_at);

  const preExitInactionMs = Math.max(0, closeTime.getTime() - lastAt.getTime());
  const sessionDurationMs = closeTime.getTime() - openAt.getTime();
  const isEarlyExit = sessionDurationMs <= EARLY_EXIT_THRESHOLD_MS;
  const isHighRiskExit =
    session.first_action_at == null ||
    preExitInactionMs >= HIGH_RISK_INACTION_MS;

  await sessionLogRepo.closeSession(
    sessionId,
    closeTime,
    preExitInactionMs,
    isHighRiskExit
  );

  logSessionEvent('app_close', {
    session_id: sessionId,
    user_id: session.user_id,
    app_open_at: session.app_open_at,
    first_action_at: session.first_action_at,
    last_action_at: session.last_action_at,
    app_close_at: closeTime,
    pre_exit_inaction_ms: preExitInactionMs,
    is_high_risk_exit: isHighRiskExit,
    reentry_latency_ms: session.reentry_latency_ms,
    action_type: session.action_type,
    session_ended: true,
  });

  return {
    session_id: sessionId,
    app_close_at: closeTime,
    pre_exit_inaction_ms: preExitInactionMs,
    is_early_exit: isEarlyExit,
    is_high_risk_exit: isHighRiskExit,
  };
}

/**
 * 첫 액션 없이 세션만 열린 경우 app_close 시 first_action_at = null 유지됨(이미 null).
 * 별도 null 처리 로직은 session_log 스키마상 이미 null이므로 생략.
 */
async function getHighRiskExitSessions(limit = 100) {
  return sessionLogRepo.findHighRiskExits(limit);
}

module.exports = {
  closeSession,
  getHighRiskExitSessions,
  EARLY_EXIT_THRESHOLD_MS,
  HIGH_RISK_INACTION_MS,
};
