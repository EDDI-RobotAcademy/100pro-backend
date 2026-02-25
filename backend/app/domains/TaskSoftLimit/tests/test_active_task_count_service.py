"""ActiveTaskCount 계산 서비스 단위 테스트."""

from unittest.mock import Mock

import pytest

from task_soft_limit.service.active_task_count_service import ActiveTaskCountService


def test_get_active_task_count_returns_provider_count():
    """provider가 반환한 값이 그대로 반환된다."""
    provider = Mock()
    provider.count_active_goals.return_value = 3
    service = ActiveTaskCountService(provider)
    assert service.get_active_task_count(user_id=1) == 3
    provider.count_active_goals.assert_called_once_with(1)


def test_get_active_task_count_zero():
    """활성 목표가 없으면 0을 반환한다."""
    provider = Mock()
    provider.count_active_goals.return_value = 0
    service = ActiveTaskCountService(provider)
    assert service.get_active_task_count(user_id=99) == 0


def test_get_active_task_count_calls_provider_with_user_id():
    """get_active_task_count는 전달한 user_id로 provider를 호출한다."""
    provider = Mock()
    provider.count_active_goals.return_value = 5
    service = ActiveTaskCountService(provider)
    service.get_active_task_count(user_id=42)
    provider.count_active_goals.assert_called_once_with(42)
