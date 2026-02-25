/**
 * [PRO-B-32] ExitAnalysisService Success Criteria 단위 테스트.
 */
jest.mock('../../../config', () => ({
  earlyExitThresholdSeconds: 60,
  highRiskExitInactionMs: 30000,
}));
jest.mock('../../repositories/sessionLogRepository');
jest.mock('../../../logger', () => ({ logSessionEvent: jest.fn() }));

const sessionLogRepo = require('../../repositories/sessionLogRepository');
const exitAnalysisService = require('../exitAnalysisService');

describe('ExitAnalysisService [PRO-B-32]', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('closeSession', () => {
    it('app_close 시 pre_exit_inaction_ms = app_close_at - last_action_at 계산', async () => {
      const sessionId = 's1';
      const lastActionAt = new Date(Date.now() - 20 * 1000);
      const appCloseAt = new Date();
      sessionLogRepo.findBySessionId.mockResolvedValue({
        session_id: sessionId,
        user_id: 'u1',
        app_open_at: new Date(Date.now() - 60 * 1000),
        first_action_at: new Date(Date.now() - 50 * 1000),
        last_action_at: lastActionAt,
        reentry_latency_ms: 10000,
        action_type: 'goal_create',
      });
      sessionLogRepo.closeSession.mockResolvedValue(undefined);

      const result = await exitAnalysisService.closeSession(
        sessionId,
        appCloseAt
      );

      expect(result.pre_exit_inaction_ms).toBeGreaterThanOrEqual(19000);
      expect(result.pre_exit_inaction_ms).toBeLessThanOrEqual(21000);
      expect(sessionLogRepo.closeSession).toHaveBeenCalledWith(
        sessionId,
        appCloseAt,
        result.pre_exit_inaction_ms,
        expect.any(Boolean)
      );
    });

    it('app_close_at - app_open_at ≤ 60초 이면 조기 이탈(is_early_exit)', async () => {
      const sessionId = 's2';
      const appOpenAt = new Date(Date.now() - 45 * 1000);
      sessionLogRepo.findBySessionId.mockResolvedValue({
        session_id: sessionId,
        user_id: 'u2',
        app_open_at: appOpenAt,
        first_action_at: null,
        last_action_at: null,
      });
      sessionLogRepo.closeSession.mockResolvedValue(undefined);

      const result = await exitAnalysisService.closeSession(sessionId);

      expect(result.is_early_exit).toBe(true);
    });

    it('진입 후 60초 초과 종료 시 is_early_exit false', async () => {
      const sessionId = 's3';
      const appOpenAt = new Date(Date.now() - 120 * 1000);
      sessionLogRepo.findBySessionId.mockResolvedValue({
        session_id: sessionId,
        user_id: 'u3',
        app_open_at: appOpenAt,
        first_action_at: new Date(Date.now() - 110 * 1000),
        last_action_at: new Date(Date.now() - 10 * 1000),
      });
      sessionLogRepo.closeSession.mockResolvedValue(undefined);

      const result = await exitAnalysisService.closeSession(sessionId);

      expect(result.is_early_exit).toBe(false);
    });

    it('pre_exit_inaction_ms가 기준값(30초) 이상이면 is_high_risk_exit = true', async () => {
      const sessionId = 's4';
      const lastActionAt = new Date(Date.now() - 35 * 1000);
      sessionLogRepo.findBySessionId.mockResolvedValue({
        session_id: sessionId,
        user_id: 'u4',
        app_open_at: new Date(Date.now() - 120 * 1000),
        first_action_at: new Date(Date.now() - 100 * 1000),
        last_action_at: lastActionAt,
      });
      sessionLogRepo.closeSession.mockResolvedValue(undefined);

      const result = await exitAnalysisService.closeSession(sessionId);

      expect(result.is_high_risk_exit).toBe(true);
      expect(sessionLogRepo.closeSession).toHaveBeenCalledWith(
        sessionId,
        expect.any(Date),
        expect.any(Number),
        true
      );
    });

    it('첫 액션 없이 종료 시 is_high_risk_exit = true', async () => {
      const sessionId = 's5';
      sessionLogRepo.findBySessionId.mockResolvedValue({
        session_id: sessionId,
        user_id: 'u5',
        app_open_at: new Date(Date.now() - 10 * 1000),
        first_action_at: null,
        last_action_at: null,
      });
      sessionLogRepo.closeSession.mockResolvedValue(undefined);

      const result = await exitAnalysisService.closeSession(sessionId);

      expect(result.is_high_risk_exit).toBe(true);
      expect(sessionLogRepo.closeSession).toHaveBeenCalledWith(
        sessionId,
        expect.any(Date),
        expect.any(Number),
        true
      );
    });

    it('세션 없으면 null 반환', async () => {
      sessionLogRepo.findBySessionId.mockResolvedValue(null);

      const result = await exitAnalysisService.closeSession('no-such');

      expect(result).toBeNull();
    });
  });
});
