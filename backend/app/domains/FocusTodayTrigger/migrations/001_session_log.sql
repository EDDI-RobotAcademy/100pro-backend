-- [PRO-B-30, PRO-B-32] session_log
-- session_id(PK), user_id, app_open_at, first_action_at, last_action_at, app_close_at,
-- reentry_latency_ms, pre_exit_inaction_ms, is_high_risk_exit, action_type

CREATE TABLE IF NOT EXISTS session_log (
  session_id     VARCHAR(36)   NOT NULL PRIMARY KEY,
  user_id        VARCHAR(36)   NOT NULL,
  app_open_at    DATETIME(3)   NOT NULL,
  first_action_at DATETIME(3)  NULL,
  last_action_at DATETIME(3)   NULL,
  app_close_at   DATETIME(3)   NULL,
  reentry_latency_ms INT       NULL COMMENT 'first_action_at - app_open_at (ms)',
  pre_exit_inaction_ms INT     NULL COMMENT 'app_close_at - last_action_at (ms)',
  is_high_risk_exit TINYINT(1) NOT NULL DEFAULT 0,
  action_type    VARCHAR(32)   NULL COMMENT 'e.g. goal_create, check',
  created_at     DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at     DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  INDEX idx_session_user_open (user_id, app_open_at),
  INDEX idx_high_risk (is_high_risk_exit),
  INDEX idx_app_close (app_close_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
