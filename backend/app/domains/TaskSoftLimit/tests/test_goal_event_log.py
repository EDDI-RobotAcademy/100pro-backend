"""GoalEventLog 엔티티 및 저장 구조 단위 테스트 (guide_exposed 기록 포함)."""

from datetime import datetime

import pytest

from task_soft_limit.domain.goal_event_log import GoalEventLog
from task_soft_limit.events import EventType, log_guide_exposed
from task_soft_limit.repository import (
    GoalEventLogRepositoryAdapter,
    InMemoryGoalEventLogRepository,
)


def test_goal_event_log_entity():
    """GoalEventLog 엔티티 필드."""
    at = datetime(2025, 2, 24, 12, 0, 0)
    log = GoalEventLog(
        user_id=1,
        event_type=EventType.GUIDE_EXPOSED,
        occurred_at=at,
        goal_id=None,
        payload={"active_task_count": 6, "guide_exposure_threshold": 6},
    )
    assert log.user_id == 1
    assert log.event_type == EventType.GUIDE_EXPOSED
    assert log.payload["active_task_count"] == 6
    assert log.id is None


def test_in_memory_repository_save():
    """InMemoryGoalEventLogRepository.save는 id를 부여하여 저장한다."""
    repo = InMemoryGoalEventLogRepository()
    log = GoalEventLog(
        user_id=1,
        event_type=EventType.TASK_CREATE,
        occurred_at=datetime.utcnow(),
        goal_id=10,
    )
    saved = repo.save(log)
    assert saved.id == 1
    assert saved.goal_id == 10
    assert len(repo.find_all()) == 1


def test_adapter_log_guide_exposed_saves_to_repository():
    """log_guide_exposed 호출 시 Adapter가 GoalEventLog로 저장한다."""
    repo = InMemoryGoalEventLogRepository()
    adapter = GoalEventLogRepositoryAdapter(repo)
    log_guide_exposed(
        adapter,
        user_id=1,
        active_task_count=6,
        guide_exposure_threshold=6,
    )
    logs = repo.find_all()
    assert len(logs) == 1
    assert logs[0].event_type == EventType.GUIDE_EXPOSED
    assert logs[0].user_id == 1
    assert logs[0].payload == {
        "active_task_count": 6,
        "guide_exposure_threshold": 6,
        "next_task_ordinal": 7,
    }
    assert logs[0].id is not None
