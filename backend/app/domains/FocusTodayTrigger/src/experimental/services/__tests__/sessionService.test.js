/**
 * [PRO-B-30] SessionService Success Criteria 단위 테스트.
 */
const { v4: uuidv4 } = require('uuid');

jest.mock('../../../db');
jest.mock('../../../logger', () => ({
  logSessionEvent: jest.fn(),
}));
jest.mock('../../repositories/sessionLogRepository');
jest.mock('../../../config', () => ({
  taskDisplayScope: 'today',
}));

const sessionLogRepo = require('../../repositories/sessionLogRepository');
const sessionService = require('../sessionService');

describe('SessionService [PRO-B-30]', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('startSession (app_open)', () => {
    it('앱 진입 이벤트 수신 시 user_id, session_id, app_open_at 이 기록된다', async () => {
      sessionLogRepo.create.mockResolvedValue(undefined);

      const result = await sessionService.startSession('user-1');

      expect(result).toHaveProperty('session_id');
      expect(result).toHaveProperty('user_id', 'user-1');
      expect(result).toHaveProperty('app_open_at');
      expect(result.app_open_at).toBeInstanceOf(Date);
      expect(sessionLogRepo.create).toHaveBeenCalledWith(
        expect.objectContaining({
          user_id: 'user-1',
          app_open_at: result.app_open_at,
        })
      );
    });
  });

  describe('recordFirstOrLastAction', () => {
    it('첫 액션 발생 시 first_action_at 기록 및 ReEntryLatency = first_action_at - app_open_at 저장', async () => {
      const sessionId = uuidv4();
      const appOpenAt = new Date(Date.now() - 15000);
      sessionLogRepo.findBySessionId.mockResolvedValue({
        session_id: sessionId,
        user_id: 'user-1',
        app_open_at: appOpenAt,
        first_action_at: null,
        last_action_at: null,
      });
      sessionLogRepo.updateFirstAction.mockResolvedValue(undefined);

      const result = await sessionService.recordFirstOrLastAction(
        sessionId,
        'goal_create'
      );

      expect(result.is_first_action).toBe(true);
      expect(result.first_action_at).toBeInstanceOf(Date);
      expect(result.reentry_latency_ms).toBeGreaterThanOrEqual(14000);
      expect(result.reentry_latency_ms).toBeLessThanOrEqual(16000);
      expect(result.action_type).toBe('goal_create');
      expect(sessionLogRepo.updateFirstAction).toHaveBeenCalledWith(
        sessionId,
        result.first_action_at,
        result.reentry_latency_ms,
        'goal_create'
      );
    });

    it('첫 액션 없이 세션만 있는 경우 first_action_at은 null 유지(이미 null)', async () => {
      const sessionId = uuidv4();
      sessionLogRepo.findBySessionId.mockResolvedValue({
        session_id: sessionId,
        user_id: 'user-1',
        app_open_at: new Date(),
        first_action_at: null,
        last_action_at: null,
      });
      sessionLogRepo.updateFirstAction.mockResolvedValue(undefined);

      await sessionService.recordFirstOrLastAction(sessionId, 'check');

      expect(sessionLogRepo.updateFirstAction).toHaveBeenCalled();
      const [, firstActionAt] = sessionLogRepo.updateFirstAction.mock.calls[0];
      expect(firstActionAt).toBeInstanceOf(Date);
    });

    it('이미 첫 액션이 있으면 last_action_at만 갱신', async () => {
      const sessionId = uuidv4();
      const existingFirst = new Date(Date.now() - 10000);
      sessionLogRepo.findBySessionId.mockResolvedValue({
        session_id: sessionId,
        user_id: 'user-1',
        app_open_at: new Date(Date.now() - 20000),
        first_action_at: existingFirst,
        last_action_at: existingFirst,
      });
      sessionLogRepo.updateLastAction.mockResolvedValue(undefined);

      const result = await sessionService.recordFirstOrLastAction(
        sessionId,
        'check'
      );

      expect(result.is_first_action).toBe(false);
      expect(result.last_action_at).toBeInstanceOf(Date);
      expect(sessionLogRepo.updateLastAction).toHaveBeenCalledWith(
        sessionId,
        result.last_action_at,
        'check'
      );
      expect(sessionLogRepo.updateFirstAction).not.toHaveBeenCalled();
    });

    it('세션이 없으면 null 반환', async () => {
      sessionLogRepo.findBySessionId.mockResolvedValue(null);

      const result = await sessionService.recordFirstOrLastAction('no-such', 'goal_create');

      expect(result).toBeNull();
    });
  });

  describe('getScopeDate', () => {
    it('TaskDisplayScope today 시 당일 YYYY-MM-DD 반환', () => {
      const date = sessionService.getScopeDate();
      expect(date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    });
  });
});
