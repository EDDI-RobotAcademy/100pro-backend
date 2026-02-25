-- [PRO-B-31] intervention_log
-- log_id(PK), user_id, session_id, experiment_group, triggered_at, first_action_after_trigger_at

CREATE TABLE IF NOT EXISTS intervention_log (
  log_id                      VARCHAR(36)   NOT NULL PRIMARY KEY,
  user_id                     VARCHAR(36)   NOT NULL,
  session_id                  VARCHAR(36)   NOT NULL,
  experiment_group            VARCHAR(16)   NOT NULL COMMENT 'experimental | control',
  triggered_at                DATETIME(3)   NOT NULL,
  first_action_after_trigger_at DATETIME(3) NULL,
  created_at                  DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at                  DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  INDEX idx_intervention_user (user_id),
  INDEX idx_intervention_session (session_id),
  INDEX idx_triggered_at (triggered_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
