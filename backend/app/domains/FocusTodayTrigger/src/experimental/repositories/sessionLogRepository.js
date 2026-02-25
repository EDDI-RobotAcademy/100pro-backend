/**
 * [PRO-B-30, PRO-B-32] session_log CRUD.
 */
const db = require('../../db');

const TABLE = 'session_log';

async function create(session) {
  await db.query(
    `INSERT INTO ${TABLE} (session_id, user_id, app_open_at, action_type)
     VALUES (?, ?, ?, ?)`,
    [
      session.session_id,
      session.user_id,
      session.app_open_at,
      session.action_type ?? null,
    ]
  );
  return session;
}

async function findByUserAndAppOpen(userId, appOpenAt) {
  return db.queryOne(
    `SELECT * FROM ${TABLE} WHERE user_id = ? AND app_open_at = ? LIMIT 1`,
    [userId, appOpenAt]
  );
}

async function findBySessionId(sessionId) {
  return db.queryOne(`SELECT * FROM ${TABLE} WHERE session_id = ?`, [sessionId]);
}

async function updateFirstAction(sessionId, firstActionAt, reentryLatencyMs, actionType) {
  await db.query(
    `UPDATE ${TABLE} SET first_action_at = ?, last_action_at = ?, reentry_latency_ms = ?, action_type = ?, updated_at = NOW(3) WHERE session_id = ?`,
    [firstActionAt, firstActionAt, reentryLatencyMs, actionType, sessionId]
  );
}

async function updateLastAction(sessionId, lastActionAt, actionType) {
  await db.query(
    `UPDATE ${TABLE} SET last_action_at = ?, action_type = ?, updated_at = NOW(3) WHERE session_id = ?`,
    [lastActionAt, actionType, sessionId]
  );
}

async function closeSession(sessionId, appCloseAt, preExitInactionMs, isHighRiskExit) {
  await db.query(
    `UPDATE ${TABLE} SET app_close_at = ?, pre_exit_inaction_ms = ?, is_high_risk_exit = ?, updated_at = NOW(3) WHERE session_id = ?`,
    [appCloseAt, preExitInactionMs, isHighRiskExit ? 1 : 0, sessionId]
  );
}

/** [PRO-B-27] TaskDisplayScope 'today': 당일 생성된 세션만. date = YYYY-MM-DD */
async function findSessionsByUserAndDate(userId, date) {
  return db.query(
    `SELECT * FROM ${TABLE} WHERE user_id = ? AND DATE(app_open_at) = ? ORDER BY app_open_at DESC`,
    [userId, date]
  );
}

async function findHighRiskExits(limit = 100) {
  return db.query(
    `SELECT * FROM ${TABLE} WHERE is_high_risk_exit = 1 ORDER BY app_close_at DESC LIMIT ?`,
    [limit]
  );
}

module.exports = {
  create,
  findByUserAndAppOpen,
  findBySessionId,
  updateFirstAction,
  updateLastAction,
  closeSession,
  findSessionsByUserAndDate,
  findHighRiskExits,
};
