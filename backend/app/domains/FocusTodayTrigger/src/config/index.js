/**
 * Application config. [PRO-B-27] TaskDisplayScope 기본값 today.
 * 환경변수로 오버라이드 가능.
 */
require('dotenv').config();

const config = {
  env: process.env.NODE_ENV || 'development',
  port: parseInt(process.env.PORT, 10) || 3000,

  mysql: {
    host: process.env.MYSQL_HOST || 'localhost',
    port: parseInt(process.env.MYSQL_PORT, 10) || 3306,
    user: process.env.MYSQL_USER || 'root',
    password: process.env.MYSQL_PASSWORD || '',
    database: process.env.MYSQL_DATABASE || 'focus_today',
  },

  /** [PRO-B-27] 당일 생성 데이터만 조회할 때 사용. 'today' | 'week' | 'all' */
  taskDisplayScope: process.env.TASK_DISPLAY_SCOPE || 'today',

  /** [PRO-B-31] 무행동 N초 초과 시 개입 트리거 (기본 30초) */
  inactionTriggerSeconds: parseInt(process.env.INACTION_TRIGGER_SECONDS, 10) || 30,

  /** [PRO-B-32] 이탈 직전 무행동이 이 값(ms) 이상이면 고위험 이탈 */
  highRiskExitInactionMs: parseInt(process.env.HIGH_RISK_EXIT_INACTION_MS, 10) || 30000,

  /** [PRO-B-32] app_open ~ app_close ≤ 이 값(초)이면 조기 이탈 */
  earlyExitThresholdSeconds: parseInt(process.env.EARLY_EXIT_THRESHOLD_SECONDS, 10) || 60,
};

module.exports = config;
