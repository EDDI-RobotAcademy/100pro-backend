/**
 * 세션/액션/종료 이벤트 API.
 */
const sessionService = require('../services/sessionService');
const exitAnalysisService = require('../services/exitAnalysisService');
const interventionService = require('../services/interventionService');

async function appOpen(req, res, next) {
  try {
    const userId = req.body?.user_id ?? req.query?.user_id;
    if (!userId) {
      return res.status(400).json({ error: 'user_id required' });
    }
    const result = await sessionService.startSession(userId);
    res.status(201).json(result);
  } catch (err) {
    next(err);
  }
}

async function recordAction(req, res, next) {
  try {
    const { session_id, action_type } = req.body ?? {};
    if (!session_id) {
      return res.status(400).json({ error: 'session_id required' });
    }
    const result = await sessionService.recordFirstOrLastAction(
      session_id,
      action_type || sessionService.ACTION_TYPES.OTHER
    );
    if (!result) {
      return res.status(404).json({ error: 'session not found' });
    }
    // 개입 트리거 이후 첫 액션인 경우 intervention_log 갱신
    if (result.is_first_action) {
      await interventionService.recordFirstActionAfterTrigger(
        session_id,
        result.first_action_at
      );
    } else {
      await interventionService.recordFirstActionAfterTrigger(
        session_id,
        result.last_action_at
      );
    }
    res.json(result);
  } catch (err) {
    next(err);
  }
}

async function appClose(req, res, next) {
  try {
    const { session_id, app_close_at } = req.body ?? {};
    if (!session_id) {
      return res.status(400).json({ error: 'session_id required' });
    }
    const result = await exitAnalysisService.closeSession(
      session_id,
      app_close_at
    );
    if (!result) {
      return res.status(404).json({ error: 'session not found' });
    }
    res.json(result);
  } catch (err) {
    next(err);
  }
}

async function getSessions(req, res, next) {
  try {
    const userId = req.params?.user_id ?? req.query?.user_id;
    if (!userId) {
      return res.status(400).json({ error: 'user_id required' });
    }
    const sessions = await sessionService.getSessionsForUserInScope(userId);
    res.json({ task_display_scope: sessionService.getScopeDate(), sessions });
  } catch (err) {
    next(err);
  }
}

module.exports = {
  appOpen,
  recordAction,
  appClose,
  getSessions,
};
