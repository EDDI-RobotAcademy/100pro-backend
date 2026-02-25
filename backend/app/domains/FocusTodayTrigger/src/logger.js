/**
 * Central logger. session_log / intervention_log 관련 필드(reentry_latency_ms, action_type 등)를
 * 구조화하여 기록할 수 있도록 사용.
 */
const winston = require('winston');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'focus-today-trigger' },
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      ),
    }),
  ],
});

/**
 * PRO-B-30: session_id, user_id, reentry_latency_ms, action_type, 세션 종료 여부 로깅
 */
function logSessionEvent(event, data) {
  logger.info('session_event', {
    event,
    session_id: data.session_id,
    user_id: data.user_id,
    reentry_latency_ms: data.reentry_latency_ms,
    action_type: data.action_type,
    session_ended: data.session_ended,
    app_open_at: data.app_open_at,
    first_action_at: data.first_action_at,
    last_action_at: data.last_action_at,
    app_close_at: data.app_close_at,
    pre_exit_inaction_ms: data.pre_exit_inaction_ms,
    is_high_risk_exit: data.is_high_risk_exit,
  });
}

/**
 * PRO-B-31: intervention_log 관련 로깅
 */
function logInterventionEvent(event, data) {
  logger.info('intervention_event', {
    event,
    user_id: data.user_id,
    session_id: data.session_id,
    experiment_group: data.experiment_group,
    triggered_at: data.triggered_at,
    first_action_after_trigger_at: data.first_action_after_trigger_at,
    log_id: data.log_id,
  });
}

module.exports = {
  logger,
  logSessionEvent,
  logInterventionEvent,
};
