"""
TaskSoftLimit — ActiveTaskCount 기반 Soft 제한 실험 인프라.

- 목표 생성은 차단하지 않음. ActiveTaskCount >= threshold 시 guide_exposed 이벤트만 기록.
- 설계: docs/ 설계서, PRD, MVP 참조.
"""

from task_soft_limit.domain import (
    ActiveGoalCountProvider,
    GoalCreateFlowResult,
    GoalEventLog,
)
from task_soft_limit.events import EventType, GoalEventLogger, log_guide_exposed
from task_soft_limit.policy import is_overload
from task_soft_limit.repository import (
    GoalEventLogRepositoryAdapter,
    InMemoryGoalEventLogRepository,
)
from task_soft_limit.service import (
    ActiveTaskCountService,
    GoalCreateService,
    OverloadCheckService,
    execute_goal_create_flow,
)
from task_soft_limit.settings import (
    get_active_task_count_cap,
    get_guide_exposure_threshold,
    get_guide_message,
)

__all__ = [
    "ActiveGoalCountProvider",
    "ActiveTaskCountService",
    "EventType",
    "GoalCreateFlowResult",
    "GoalCreateService",
    "GoalEventLog",
    "GoalEventLogRepositoryAdapter",
    "GoalEventLogger",
    "InMemoryGoalEventLogRepository",
    "OverloadCheckService",
    "execute_goal_create_flow",
    "get_active_task_count_cap",
    "get_guide_exposure_threshold",
    "get_guide_message",
    "is_overload",
    "log_guide_exposed",
]
