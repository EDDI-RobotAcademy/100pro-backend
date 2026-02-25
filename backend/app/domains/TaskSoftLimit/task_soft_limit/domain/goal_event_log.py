"""GoalEventLog 엔티티 (설계서 §1.3)."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from task_soft_limit.events.event_type import EventType


@dataclass
class GoalEventLog:
    """
    사용자/시스템 행동 추적 및 실험 분석을 위한 이벤트 로그 엔티티.
    """

    user_id: int
    event_type: EventType
    occurred_at: datetime
    goal_id: Optional[int] = None
    payload: Optional[dict[str, Any]] = None
    id: Optional[int] = None  # 저장 후 부여되는 PK (선택)
