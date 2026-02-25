"""
ActiveTaskCount 계산 서비스.
user_id 기준 현재 활성 목표 수를 반환한다.
"""

from task_soft_limit.domain.active_goal_count_provider import ActiveGoalCountProvider


class ActiveTaskCountService:
    """ActiveTaskCount 계산 서비스. 제공자(Provider)를 주입받아 현재 활성 목표 수를 반환한다."""

    def __init__(self, provider: ActiveGoalCountProvider) -> None:
        self._provider = provider

    def get_active_task_count(self, user_id: int) -> int:
        """
        user_id 기준 현재 활성 목표 수를 반환한다.

        Args:
            user_id: 목표 소유자 사용자 ID.

        Returns:
            당일·활성 상태인 목표 개수.
        """
        return self._provider.count_active_goals(user_id)
