"""
GoalEventLog 저장 구조.
Protocol + InMemory 구현. guide_exposed 등 이벤트 기록 시 사용.
"""

from datetime import datetime
from typing import Any, Optional, Protocol

from task_soft_limit.domain.goal_event_log import GoalEventLog
from task_soft_limit.events.event_type import EventType


class GoalEventLogRepository(Protocol):
    """GoalEventLog 저장 프로토콜."""

    def save(self, log: GoalEventLog) -> GoalEventLog:
        """이벤트 로그 한 건 저장. 저장된 엔티티( id 부여됨) 반환."""
        ...


class InMemoryGoalEventLogRepository:
    """GoalEventLog 인메모리 저장 구현. 테스트 및 단일 프로세스용."""

    def __init__(self) -> None:
        self._logs: list[GoalEventLog] = []
        self._next_id = 1

    def save(self, log: GoalEventLog) -> GoalEventLog:
        new_id = self._next_id
        self._next_id += 1
        saved = GoalEventLog(
            id=new_id,
            user_id=log.user_id,
            event_type=log.event_type,
            goal_id=log.goal_id,
            payload=log.payload,
            occurred_at=log.occurred_at,
        )
        self._logs.append(saved)
        return saved

    def find_all(self) -> list[GoalEventLog]:
        """저장된 로그 전체 반환 (테스트/검증용)."""
        return list(self._logs)


class GoalEventLogRepositoryAdapter:
    """
    GoalEventLogger 프로토콜 구현체.
    log() 호출을 GoalEventLog 엔티티로 변환하여 Repository에 저장한다.
    guide_exposed 이벤트 기록 포함.
    """

    def __init__(self, repository: GoalEventLogRepository) -> None:
        self._repository = repository

    def log(
        self,
        user_id: int,
        event_type: EventType,
        *,
        goal_id: Optional[int] = None,
        payload: Optional[dict[str, Any]] = None,
        occurred_at: Optional[datetime] = None,
    ) -> None:
        if occurred_at is None:
            occurred_at = datetime.utcnow()
        log = GoalEventLog(
            user_id=user_id,
            event_type=event_type,
            goal_id=goal_id,
            payload=payload,
            occurred_at=occurred_at,
        )
        self._repository.save(log)
