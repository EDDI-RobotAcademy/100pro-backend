"""TaskSoftLimit 단위 테스트: 과부하 판별, 생성 흐름, 이벤트 기록."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from task_soft_limit.events import EventType, log_guide_exposed
from task_soft_limit.policy import is_overload
from task_soft_limit.service import execute_goal_create_flow
from task_soft_limit.settings import (
    get_active_task_count_cap,
    get_guide_exposure_threshold,
    get_guide_message,
)


# --- settings ---


def test_get_guide_exposure_threshold_default():
    """기본 threshold는 6."""
    assert get_guide_exposure_threshold() == 6


def test_get_active_task_count_cap_default():
    """기본 cap은 5."""
    assert get_active_task_count_cap() == 5


def test_get_guide_message_uses_cap():
    """가이드 메시지는 Cap 기준 문구 반환 (Parameter Backlog)."""
    assert get_guide_message() == "오늘 목표는 최대 5개가 적절해요"


# --- overload ---


def test_is_overload_false_when_below_threshold():
    """active_task_count < 6 이면 과부하 아님."""
    assert is_overload(5) is False
    assert is_overload(0) is False


def test_is_overload_true_when_at_or_above_threshold():
    """active_task_count >= 6 이면 과부하."""
    assert is_overload(6) is True
    assert is_overload(7) is True


def test_is_overload_respects_custom_threshold():
    """threshold 인자로 6 이외 값 사용 가능."""
    assert is_overload(4, threshold=5) is False
    assert is_overload(5, threshold=5) is True


# --- guide_exposed logging ---


def test_log_guide_exposed_calls_logger():
    """log_guide_exposed는 logger.log를 GUIDE_EXPOSED와 payload로 호출."""
    logger = Mock()
    log_guide_exposed(logger, user_id=1, active_task_count=6, guide_exposure_threshold=6)
    logger.log.assert_called_once()
    call = logger.log.call_args
    assert call.kwargs["event_type"] == EventType.GUIDE_EXPOSED
    assert call.kwargs["goal_id"] is None
    assert call.kwargs["payload"] == {
        "active_task_count": 6,
        "guide_exposure_threshold": 6,
    }
    assert call.args[0] == 1


# --- goal create flow ---


def test_execute_goal_create_flow_not_overload():
    """active_task_count 5 → guide_exposed 기록 안 함, 생성 허용."""
    logger = Mock()
    result = execute_goal_create_flow(
        user_id=1,
        active_task_count=5,
        event_logger=logger,
    )
    assert result.guide_exposed is False
    assert result.guide_message is None
    logger.log.assert_not_called()


def test_execute_goal_create_flow_overload():
    """active_task_count 6 → guide_exposed 기록, 가이드 메시지 반환, 생성 허용."""
    logger = Mock()
    result = execute_goal_create_flow(
        user_id=1,
        active_task_count=6,
        event_logger=logger,
    )
    assert result.guide_exposed is True
    assert result.guide_message == "오늘 목표는 최대 5개가 적절해요"
    logger.log.assert_called_once()
    call = logger.log.call_args
    assert call.kwargs["event_type"] == EventType.GUIDE_EXPOSED
    assert call.kwargs["payload"]["active_task_count"] == 6
    assert call.kwargs["payload"]["next_task_ordinal"] == 7


def test_execute_goal_create_flow_uses_custom_threshold():
    """threshold=5 이면 active_task_count 5에서도 guide_exposed."""
    logger = Mock()
    result = execute_goal_create_flow(
        user_id=1,
        active_task_count=5,
        event_logger=logger,
        threshold=5,
    )
    assert result.guide_exposed is True
    assert result.guide_message is not None
    assert logger.log.call_args.kwargs["payload"]["guide_exposure_threshold"] == 5
    assert logger.log.call_args.kwargs["payload"]["next_task_ordinal"] == 6


def test_execute_goal_create_flow_occurred_at():
    """occurred_at 전달 시 이벤트 시각으로 사용."""
    logger = Mock()
    at = datetime(2025, 2, 24, 12, 0, 0)
    execute_goal_create_flow(
        user_id=1,
        active_task_count=6,
        event_logger=logger,
        occurred_at=at,
    )
    assert logger.log.call_args.kwargs["occurred_at"] == at
