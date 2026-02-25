/**
 * [PRO-B-31] 사용자 단위 실험군/대조군 분기.
 * 실험군(experimental)에만 개입 트리거 발행, 대조군(control)은 개입 없음.
 */
const EXPERIMENTAL = 'experimental';
const CONTROL = 'control';

/**
 * user_id 기반 안정적 해시로 A/B 그룹 결정 (50/50).
 * 동일 user_id는 항상 같은 그룹.
 */
function getExperimentGroup(userId) {
  if (!userId) return CONTROL;
  let hash = 0;
  const str = String(userId);
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash;
  }
  return Math.abs(hash) % 2 === 0 ? EXPERIMENTAL : CONTROL;
}

function isExperimental(userId) {
  return getExperimentGroup(userId) === EXPERIMENTAL;
}

module.exports = {
  EXPERIMENTAL,
  CONTROL,
  getExperimentGroup,
  isExperimental,
};
