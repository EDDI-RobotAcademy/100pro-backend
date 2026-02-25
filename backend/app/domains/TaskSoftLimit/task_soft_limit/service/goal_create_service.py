"""
목표 생성 서비스.
처리 순서: 1) ActiveTaskCount 계산 2) 과부하 판별 3) guide_exposed 노출 및 기록 4) 목표 생성 허용.
"""

from datetime import datetime

from task_soft_limit.domain.result import GoalCreateFlowResult
from task_soft_limit.events.logging import GoalEventLogger, log_guide_exposed
from task_soft_limit.service.active_task_count_service import ActiveTaskCountService
from task_soft_limit.service.overload_check_service import OverloadCheckService
from task_soft_limit.settings import get_guide_exposure_threshold, get_guide_message


class GoalCreateService:
    """
    목표 생성 처리 서비스.
    ActiveTaskCount 계산 → 과부하 판별 → guide_exposed 기록(과부하 시) → 생성 허용(항상).
    """

    def __init__(
        self,
        active_task_count_service: ActiveTaskCountService,
        overload_check_service: OverloadCheckService,
        event_logger: GoalEventLogger,
    ) -> None:
        self._active_task_count_service = active_task_count_service
        self._overload_check_service = overload_check_service
        self._event_logger = event_logger

    def execute(
        self,
        user_id: int,
        *,
        occurred_at: datetime | None = None,
    ) -> GoalCreateFlowResult:
        """
        목표 생성 흐름 실행.
        1) ActiveTaskCount 계산
        2) 과부하 판별 (설정값 threshold)
        3) 과부하이면 guide_exposed 노출 및 기록
        4) 목표 생성 허용 (항상)

        Args:
            user_id: 목표 소유자 사용자 ID.
            occurred_at: 이벤트 발생 시각. None이면 현재 시각 사용.

        Returns:
            GoalCreateFlowResult(guide_exposed=True/False). 생성은 항상 허용된다.
        """
        # 1) ActiveTaskCount 계산
        active_task_count = self._active_task_count_service.get_active_task_count(user_id)
        # 2) 과부하 판별
        overload = self._overload_check_service.is_overload(active_task_count)
        # 3) guide_exposed 노출 및 기록
        if overload:
            threshold = get_guide_exposure_threshold()
            log_guide_exposed(
                self._event_logger,
                user_id,
                active_task_count,
                threshold,
                occurred_at=occurred_at,
            )
            # 4) 목표 생성 허용 + 가이드 응답 반환 (Parameter Backlog)
            return GoalCreateFlowResult(
                guide_exposed=True,
                guide_message=get_guide_message(),
            )
        # 4) 목표 생성 허용
        return GoalCreateFlowResult(guide_exposed=False, guide_message=None)
