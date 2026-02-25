/**
 * [PRO-B-31] 개입 트리거 및 포커스 상태 API.
 */
const interventionService = require('../services/interventionService');

/**
 * 무행동 초과 시 실험군만 개입 트리거. 인터랙션 클릭 후 목표 입력창 포커싱을 위한 상태 반환.
 * GET/POST /experimental/intervention/state?user_id=...&session_id=...
 */
async function getInterventionState(req, res, next) {
  try {
    const userId = req.body?.user_id ?? req.query?.user_id;
    const sessionId = req.body?.session_id ?? req.query?.session_id;
    if (!userId || !sessionId) {
      return res.status(400).json({
        error: 'user_id and session_id required',
        focus_input: false,
      });
    }
    const state = await interventionService.getInterventionState(
      userId,
      sessionId
    );
    res.json(state);
  } catch (err) {
    next(err);
  }
}

/**
 * 클라이언트 30초 타이머 만료 시 호출: 무행동 초과 여부 확인 후 실험군이면 개입 발행.
 * POST /experimental/intervention/check
 */
async function checkInaction(req, res, next) {
  try {
    const { user_id, session_id } = req.body ?? {};
    if (!user_id || !session_id) {
      return res.status(400).json({ error: 'user_id and session_id required' });
    }
    const result = await interventionService.checkAndTriggerIntervention(
      user_id,
      session_id
    );
    res.json(result);
  } catch (err) {
    next(err);
  }
}

module.exports = {
  getInterventionState,
  checkInaction,
};
