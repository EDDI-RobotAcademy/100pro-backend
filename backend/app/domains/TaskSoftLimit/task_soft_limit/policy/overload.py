"""
과부하 판별: ActiveTaskCount >= guide_exposure_threshold (설계서 §3).

ActiveTaskCount는 호출 측에서 당일·활성 목표 수로 계산하여 전달한다.
"""

from task_soft_limit.settings import get_guide_exposure_threshold


def is_overload(
    active_task_count: int,
    *,
    threshold: int | None = None,
) -> bool:
    """
    현재 활성 목표 수가 가이드 노출 임계값 이상이면 True.

    Args:
        active_task_count: 당일·활성 상태인 목표 개수
        threshold: 사용할 임계값. None이면 설정값(get_guide_exposure_threshold) 사용.

    Returns:
        active_task_count >= threshold 이면 True (과부하).
    """
    if threshold is None:
        threshold = get_guide_exposure_threshold()
    return active_task_count >= threshold
