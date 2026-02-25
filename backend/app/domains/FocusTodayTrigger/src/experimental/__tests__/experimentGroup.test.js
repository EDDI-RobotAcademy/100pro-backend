/**
 * [PRO-B-31] 실험군/대조군 분기 안정성.
 */
const {
  getExperimentGroup,
  isExperimental,
  EXPERIMENTAL,
  CONTROL,
} = require('../experimentGroup');

describe('experimentGroup', () => {
  it('동일 user_id는 항상 같은 그룹 반환', () => {
    const userId = 'user-abc-123';
    const a = getExperimentGroup(userId);
    const b = getExperimentGroup(userId);
    expect(a).toBe(b);
    expect([EXPERIMENTAL, CONTROL]).toContain(a);
  });

  it('isExperimental은 experimental 그룹일 때만 true', () => {
    const experimentalUserId = [...Array(20)]
      .map((_, i) => `user-${i}`)
      .find((id) => getExperimentGroup(id) === EXPERIMENTAL);
    const controlUserId = [...Array(20)]
      .map((_, i) => `user-${i}`)
      .find((id) => getExperimentGroup(id) === CONTROL);
    if (experimentalUserId) {
      expect(isExperimental(experimentalUserId)).toBe(true);
    }
    if (controlUserId) {
      expect(isExperimental(controlUserId)).toBe(false);
    }
  });

  it('user_id 없으면 control', () => {
    expect(getExperimentGroup(null)).toBe(CONTROL);
    expect(getExperimentGroup('')).toBe(CONTROL);
  });
});
