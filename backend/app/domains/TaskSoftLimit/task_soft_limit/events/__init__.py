"""이벤트 로깅: EventType, 기록 인터페이스 (설계서 §2)."""

from task_soft_limit.events.event_type import EventType
from task_soft_limit.events.logging import GoalEventLogger, log_guide_exposed

__all__ = [
    "EventType",
    "GoalEventLogger",
    "log_guide_exposed",
]
