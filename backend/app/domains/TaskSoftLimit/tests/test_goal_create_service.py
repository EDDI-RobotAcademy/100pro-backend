"""목표 생성 서비스 단위 테스트 (1~4 순서 흐름)."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from task_soft_limit.events import EventType
from task_soft_limit.repository import (
    GoalEventLogRepositoryAdapter,
    InMemoryGoalEventLogRepository,
)
from task_soft_limit.service.active_task_count_service import ActiveTaskCountService
from task_soft_limit.service.goal_create_service import GoalCreateService
from task_soft_limit.service.overload_check_service import OverloadCheckService


def _make_service(active_count: int):
    """ActiveTaskCount=active_count를 반환하는 provider로 서비스 조립."""
    provider = Mock()
    provider.count_active_goals.return_value = active_count
    active_task_count_service = ActiveTaskCountService(provider)
    overload_check_service = OverloadCheckService()
    repo = InMemoryGoalEventLogRepository()
    event_logger = GoalEventLogRepositoryAdapter(repo)
    return GoalCreateService(
        active_task_count_service=active_task_count_service,
        overload_check_service=overload_check_service,
        event_logger=event_logger,
    ), repo


def test_execute_flow_not_overload():
    """ActiveTaskCount 5 → 과부하 아님 → guide_exposed 미기록, 생성 허용."""
    service, repo = _make_service(5)
    result = service.execute(user_id=1)
    assert result.guide_exposed is False
    assert result.guide_message is None
    assert len(repo.find_all()) == 0


def test_execute_flow_overload_records_guide_exposed():
    """ActiveTaskCount 6 → 과부하 → guide_exposed 기록, 가이드 메시지 반환, 생성 허용."""
    service, repo = _make_service(6)
    result = service.execute(user_id=1)
    assert result.guide_exposed is True
    assert result.guide_message == "오늘 목표는 최대 5개가 적절해요"
    logs = repo.find_all()
    assert len(logs) == 1
    assert logs[0].event_type == EventType.GUIDE_EXPOSED
    assert logs[0].payload["active_task_count"] == 6


def test_execute_flow_order():
    """처리 순서: 1) count 2) overload check 3) record 4) allow."""
    provider = Mock()
    provider.count_active_goals.return_value = 6
    active_svc = ActiveTaskCountService(provider)
    overload_svc = OverloadCheckService()
    repo = InMemoryGoalEventLogRepository()
    event_logger = GoalEventLogRepositoryAdapter(repo)
    service = GoalCreateService(active_svc, overload_svc, event_logger)
    service.execute(user_id=42)
    provider.count_active_goals.assert_called_once_with(42)
    assert len(repo.find_all()) == 1
