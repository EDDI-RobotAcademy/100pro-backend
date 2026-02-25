"""
TodayFocus API 라우터 [PM-TF-PAR-01, PM-TF-INF-01 STEP 2].
홈 화면 할 일 조회, app_open 이벤트 수신(세션 생성) 엔드포인트.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Path

from app.domains.task.schemas import TaskResponse
from app.domains.TodayFocus.today_focus.schemas import (
    ActionRequest,
    AppCloseRequest,
    AppOpenRequest,
    AppOpenResponse,
)
from app.domains.TodayFocus.today_focus.service import TodayFocusServiceImpl
from app.infrastructure.task_strategy.schemas import ActiveTaskListResponse

router = APIRouter()

_today_focus_service: TodayFocusServiceImpl | None = None


def _get_today_focus_service() -> TodayFocusServiceImpl:
    global _today_focus_service
    if _today_focus_service is None:
        _today_focus_service = TodayFocusServiceImpl()
    return _today_focus_service


@router.post(
    "/session/app-open",
    response_model=AppOpenResponse,
    status_code=201,
    summary="[PM-TF-INF-01] app_open 이벤트 — 세션 생성(experiment_group=A)",
)
def app_open(body: AppOpenRequest) -> AppOpenResponse:
    """app_open 이벤트 수신 시 session_log 1건 생성. Controller는 정책/쿼리 없이 Service만 호출."""
    service = _get_today_focus_service()
    app_open_at = body.app_open_at if body.app_open_at is not None else datetime.now(timezone.utc)
    if getattr(app_open_at, "tzinfo", None) is not None:
        app_open_at = app_open_at.astimezone(timezone.utc).replace(tzinfo=None)
    session_log = service.record_app_open(body.user_id, app_open_at)
    return AppOpenResponse.model_validate(session_log)


@router.post("/session/action", status_code=204, summary="[PM-TF-INF-02 STEP 3] 액션 이벤트")
def record_action(body: ActionRequest) -> None:
    service = _get_today_focus_service()
    action_at = datetime.now(timezone.utc).replace(tzinfo=None)
    service.record_action(body.session_id, action_at)


@router.post(
    "/session/app-close",
    status_code=204,
    summary="[PM-TF-INF-03 STEP 4] app_close 이벤트 — app_close_at, pre_exit_inaction_ms, is_high_risk_exit 기록",
)
def app_close(body: AppCloseRequest) -> None:
    """app_close 이벤트 수신 시 session_log UPDATE. Controller는 정책/쿼리 없이 Service만 호출."""
    service = _get_today_focus_service()
    app_close_at = body.app_close_at if body.app_close_at is not None else datetime.now(timezone.utc)
    if getattr(app_close_at, "tzinfo", None) is not None:
        app_close_at = app_close_at.astimezone(timezone.utc).replace(tzinfo=None)
    service.record_app_close(body.session_id, app_close_at)


@router.get(
    "/users/{user_id}/active-tasks",
    response_model=ActiveTaskListResponse,
    summary="[PRO-B-21] 활성 과업 목록 조회 (보관 제외, PM-TF-PAR-01 today 범위 적용)",
)
def get_active_tasks(
    user_id: str = Path(..., description="사용자 식별자"),
) -> ActiveTaskListResponse:
    """TaskDisplayScope(today)에 따라 홈에 표시할 과업만 반환. 오늘 할 일 없으면 빈 리스트."""
    service = _get_today_focus_service()
    tasks = service.get_home_tasks(user_id)
    task_dtos = [TaskResponse.model_validate(t) for t in tasks]
    return ActiveTaskListResponse(
        user_id=user_id,
        total_count=len(task_dtos),
        tasks=task_dtos,
        timestamp=datetime.now(timezone.utc),
    )
