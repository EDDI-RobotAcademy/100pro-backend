"""
과부하 판별 서비스.
ActiveTaskCount와 설정값 기반 threshold를 비교하여 과부하 상태 여부를 반환한다.
"""

from task_soft_limit.policy.overload import is_overload
from task_soft_limit.settings import get_guide_exposure_threshold


class OverloadCheckService:
    """과부하 판별 서비스. 설정값(GUIDE_EXPOSURE_THRESHOLD) 기반 threshold를 사용한다."""

    def is_overload(self, active_task_count: int) -> bool:
        """
        ActiveTaskCount가 threshold 이상이면 과부하로 판별한다.

        Args:
            active_task_count: 현재 활성 목표 수.

        Returns:
            active_task_count >= threshold 이면 True.
        """
        threshold = get_guide_exposure_threshold()
        return is_overload(active_task_count, threshold=threshold)
