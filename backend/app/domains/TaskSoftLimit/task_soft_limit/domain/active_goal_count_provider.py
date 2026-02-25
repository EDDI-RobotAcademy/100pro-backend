"""
활성 목표 수 제공 프로토콜.
user_id 기준 당일·활성 목표 수를 외부(저장소)에서 주입받기 위한 인터페이스.
"""

from typing import Protocol


class ActiveGoalCountProvider(Protocol):
    """user_id 기준 현재 활성 목표 수를 반환하는 프로토콜."""

    def count_active_goals(self, user_id: int) -> int:
        """
        해당 사용자의 현재 활성 목표 수를 반환한다.
        당일·활성(status=active) 목표만 카운트한다.
        """
        ...
