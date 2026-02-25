"""이벤트 기록 인터페이스 및 guide_exposed 기록 헬퍼 (설계서 §2)."""

from datetime import datetime
from typing import Any, Optional, Protocol

from task_soft_limit.events.event_type import EventType


class GoalEventLogger(Protocol):
    """
    GoalEventLog 저장 프로토콜.
    호출 측(백엔드)에서 구현하여 주입한다.
    """

    def log(
        self,
        user_id: int,
        event_type: EventType,
        *,
        goal_id: Optional[int] = None,
        payload: Optional[dict[str, Any]] = None,
        occurred_at: Optional[datetime] = None,
    ) -> None:
        """이벤트 한 건 기록."""
        ...


def log_guide_exposed(
    logger: GoalEventLogger,
    user_id: int,
    active_task_count: int,
    guide_exposure_threshold: int,
    *,
    occurred_at: Optional[datetime] = None,
) -> None:
    """
    과부하 시 guide_exposed 이벤트 기록 (설계서 §2.2 payload 예시).
    next_task_ordinal: 생성 시도 순서(6번째 목표 생성 시도 분석 시점 고정용).
    """
    next_task_ordinal = active_task_count + 1
    logger.log(
        user_id,
        EventType.GUIDE_EXPOSED,
        goal_id=None,
        payload={
            "active_task_count": active_task_count,
            "guide_exposure_threshold": guide_exposure_threshold,
            "next_task_ordinal": next_task_ordinal,
        },
        occurred_at=occurred_at or datetime.utcnow(),
    )
