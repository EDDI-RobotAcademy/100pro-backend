"""이벤트 타입 정의 (설계서 §2.1)."""

from enum import Enum


class EventType(str, Enum):
    """GoalEventLog에 기록되는 이벤트 종류."""

    GUIDE_EXPOSED = "guide_exposed"
    TASK_CREATE = "task_create"
    TASK_MODIFY = "task_modify"
    APP_CLOSE = "app_close"
    TASK_COMPLETE = "task_complete"
