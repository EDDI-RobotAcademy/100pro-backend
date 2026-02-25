"""
목표 생성 처리 흐름: 계산 → 과부하 판별 → 이벤트 기록 → 생성 허용 (설계서 §4).

생성은 차단하지 않음. 과부하 시 guide_exposed만 기록하고 흐름 반환.
"""

from datetime import datetime

from task_soft_limit.domain.result import GoalCreateFlowResult
from task_soft_limit.events.logging import GoalEventLogger, log_guide_exposed
from task_soft_limit.policy.overload import is_overload
from task_soft_limit.settings import get_guide_exposure_threshold, get_guide_message


def execute_goal_create_flow(
    user_id: int,
    active_task_count: int,
    event_logger: GoalEventLogger,
    *,
    threshold: int | None = None,
    occurred_at: datetime | None = None,
) -> GoalCreateFlowResult:
    """
    목표 생성 시점에 실행할 흐름.
    1) 과부하 판별 2) 과부하이면 guide_exposed 기록 3) 생성 허용(결과 반환).

    Args:
        user_id: 목표 소유자 ID
        active_task_count: 당일·활성 목표 수 (호출 측에서 계산한 값)
        event_logger: 이벤트 기록 구현체
        threshold: 가이드 노출 임계값. None이면 설정값 사용.
        occurred_at: 이벤트 발생 시각. None이면 utcnow() 사용.

    Returns:
        GoalCreateFlowResult(guide_exposed=True/False).
        호출 측에서 목표를 저장한 뒤 task_create 이벤트를 기록하고 응답한다.
    """
    if threshold is None:
        threshold = get_guide_exposure_threshold()

    overload = is_overload(active_task_count, threshold=threshold)
    if overload:
        log_guide_exposed(
            event_logger,
            user_id,
            active_task_count,
            threshold,
            occurred_at=occurred_at,
        )
        return GoalCreateFlowResult(
            guide_exposed=True,
            guide_message=get_guide_message(),
        )
    return GoalCreateFlowResult(guide_exposed=False, guide_message=None)
