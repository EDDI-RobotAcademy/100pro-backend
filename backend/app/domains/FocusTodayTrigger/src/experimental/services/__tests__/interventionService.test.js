/**
 * [PRO-B-31] InterventionService Success Criteria 단위 테스트.
 */
jest.mock('../../../config', () => ({
  inactionTriggerSeconds: 30,
}));
jest.mock('../../repositories/sessionLogRepository');
jest.mock('../../repositories/interventionLogRepository');
jest.mock('../../experimentGroup');
jest.mock('../../../logger', () => ({ logInterventionEvent: jest.fn() }));

const sessionLogRepo = require('../../repositories/sessionLogRepository');
const interventionLogRepo = require('../../repositories/interventionLogRepository');
const { getExperimentGroup, isExperimental } = require('../../experimentGroup');
const interventionService = require('../interventionService');

describe('InterventionService [PRO-B-31]', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('shouldTriggerInaction', () => {
    it('무행동 경과가 InactionTriggerSeconds(30초) 미만이면 트리거 안 함', () => {
      const session = {
        app_open_at: new Date(Date.now() - 20 * 1000),
        first_action_at: null,
        last_action_at: null,
      };
      expect(interventionService.shouldTriggerInaction(session)).toBe(false);
    });

    it('무행동 경과가 InactionTriggerSeconds(30초) 이상이면 트리거', () => {
      const session = {
        app_open_at: new Date(Date.now() - 35 * 1000),
        first_action_at: null,
        last_action_at: null,
      };
      expect(interventionService.shouldTriggerInaction(session)).toBe(true);
    });

    it('첫 액션 후 last_action_at 기준으로 무행동 계산', () => {
      const session = {
        app_open_at: new Date(Date.now() - 60 * 1000),
        first_action_at: new Date(Date.now() - 35 * 1000),
        last_action_at: new Date(Date.now() - 35 * 1000),
      };
      expect(interventionService.shouldTriggerInaction(session)).toBe(true);
    });
  });

  describe('checkAndTriggerIntervention', () => {
    it('실험군일 때만 개입 트리거 발행 및 intervention_log 기록', async () => {
      getExperimentGroup.mockReturnValue('experimental');
      isExperimental.mockReturnValue(true);
      const session = {
        session_id: 's1',
        user_id: 'u1',
        app_open_at: new Date(Date.now() - 40 * 1000),
        first_action_at: null,
        last_action_at: null,
      };
      sessionLogRepo.findBySessionId.mockResolvedValue(session);
      interventionLogRepo.findLatestBySession.mockResolvedValue(null);
      interventionLogRepo.create.mockResolvedValue(undefined);

      const result = await interventionService.checkAndTriggerIntervention(
        'u1',
        's1'
      );

      expect(result.triggered).toBe(true);
      expect(result.experiment_group).toBe('experimental');
      expect(result.focus_input).toBe(true);
      expect(interventionLogRepo.create).toHaveBeenCalledWith(
        expect.objectContaining({
          user_id: 'u1',
          session_id: 's1',
          experiment_group: 'experimental',
        })
      );
    });

    it('대조군이면 개입 없이 triggered false', async () => {
      getExperimentGroup.mockReturnValue('control');
      isExperimental.mockReturnValue(false);
      const session = {
        session_id: 's2',
        user_id: 'u2',
        app_open_at: new Date(Date.now() - 40 * 1000),
        first_action_at: null,
        last_action_at: null,
      };
      sessionLogRepo.findBySessionId.mockResolvedValue(session);
      interventionLogRepo.findLatestBySession.mockResolvedValue(null);

      const result = await interventionService.checkAndTriggerIntervention(
        'u2',
        's2'
      );

      expect(result.triggered).toBe(false);
      expect(result.experiment_group).toBe('control');
      expect(interventionLogRepo.create).not.toHaveBeenCalled();
    });

    it('무행동 미달이면 트리거 안 함', async () => {
      getExperimentGroup.mockReturnValue('experimental');
      isExperimental.mockReturnValue(true);
      const session = {
        session_id: 's3',
        user_id: 'u3',
        app_open_at: new Date(Date.now() - 10 * 1000),
        first_action_at: null,
        last_action_at: null,
      };
      sessionLogRepo.findBySessionId.mockResolvedValue(session);

      const result = await interventionService.checkAndTriggerIntervention(
        'u3',
        's3'
      );

      expect(result.triggered).toBe(false);
      expect(interventionLogRepo.create).not.toHaveBeenCalled();
    });
  });

  describe('getInterventionState', () => {
    it('focus_input 상태 반환하여 클라이언트가 목표 입력창 포커싱 가능', async () => {
      getExperimentGroup.mockReturnValue('experimental');
      isExperimental.mockReturnValue(true);
      sessionLogRepo.findBySessionId.mockResolvedValue({
        session_id: 's4',
        app_open_at: new Date(Date.now() - 40 * 1000),
        first_action_at: null,
        last_action_at: null,
      });
      interventionLogRepo.findLatestBySession.mockResolvedValue(null);
      interventionLogRepo.create.mockResolvedValue(undefined);

      const state = await interventionService.getInterventionState('u4', 's4');

      expect(state).toHaveProperty('focus_input');
      expect(state).toHaveProperty('experiment_group');
      expect(state).toHaveProperty('triggered');
      expect(state).toHaveProperty('log_id');
    });
  });
});
