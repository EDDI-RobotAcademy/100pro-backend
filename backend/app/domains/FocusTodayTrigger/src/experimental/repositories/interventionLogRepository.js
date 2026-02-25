/**
 * [PRO-B-31] intervention_log CRUD.
 */
const db = require('../../db');

const TABLE = 'intervention_log';

async function create(record) {
  await db.query(
    `INSERT INTO ${TABLE} (log_id, user_id, session_id, experiment_group, triggered_at)
     VALUES (?, ?, ?, ?, ?)`,
    [
      record.log_id,
      record.user_id,
      record.session_id,
      record.experiment_group,
      record.triggered_at,
    ]
  );
  return record;
}

async function updateFirstActionAfterTrigger(logId, firstActionAfterTriggerAt) {
  await db.query(
    `UPDATE ${TABLE} SET first_action_after_trigger_at = ?, updated_at = NOW(3) WHERE log_id = ?`,
    [firstActionAfterTriggerAt, logId]
  );
}

async function findBySessionId(sessionId) {
  return db.query(
    `SELECT * FROM ${TABLE} WHERE session_id = ? ORDER BY triggered_at DESC`,
    [sessionId]
  );
}

async function findLatestBySession(sessionId) {
  return db.queryOne(
    `SELECT * FROM ${TABLE} WHERE session_id = ? ORDER BY triggered_at DESC LIMIT 1`,
    [sessionId]
  );
}

module.exports = {
  create,
  updateFirstActionAfterTrigger,
  findBySessionId,
  findLatestBySession,
};
