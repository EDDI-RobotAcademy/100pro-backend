"""
[PRO-B-41] Chain·일일 성취 및 성공 기준 검증 API.
ChainLength 조회, DailyCompletion, calendar_view/dwell_time 로깅, 활성 사용자 세그먼트.
"""
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.domains.auth.models import User
from app.domains.auth.security import get_current_user
from app.infrastructure.chain.chain_manager import ChainManager
from app.infrastructure.chain.schemas import (
    CalendarDayEntry,
    CalendarMonthResponse,
    ChainAnalyticsEventType,
    ChainStateResponse,
    ChainUpdateResult,
    DailyCompletionResponse,
    RecordAppLifecycleRequest,
    RecordCalendarViewRequest,
    RecordCompletionRequest,
    RecordCompletionResponse,
    RecordStickerExposedRequest,
    StickerGradeResponse,
)
from app.infrastructure.chain.service import ChainServiceImpl
from app.infrastructure.chain.sticker_config import get_max_active_task_count, get_sticker_grade

router = APIRouter()

_service: ChainServiceImpl | None = None


def _get_service() -> ChainServiceImpl:
    global _service
    if _service is None:
        _service = ChainServiceImpl()
    return _service


# ── [PRO-B-44] 서버 기반 집계·기간 조회·동기화 ─────────────────────────────────────

@router.get(
    "/calendar",
    response_model=CalendarMonthResponse,
    summary="[PRO-B-44] 특정 달(Month) 기록 조회 — 날짜별 완료 수·스티커 등급 ID 배열",
)
def get_calendar_month(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
):
    """[PRO-B-44] GET /calendar?year=2024&month=05 — 사용자 환경 간 데이터 정합성·정확한 기간 조회."""
    if not (1 <= month <= 12):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="month must be 1-12")
    entries = ChainManager.get_month_calendar(current_user.id, year, month)
    return CalendarMonthResponse(
        year=year,
        month=month,
        days=[CalendarDayEntry(date=e.date, completed_count=e.completed_count, sticker_grade_id=e.sticker_grade_id) for e in entries],
    )


@router.post(
    "/recompute",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[PRO-B-44] 재집계 — Raw Event 기준으로 일별·Chain 재계산 (순수 함수형, 동일 결과 보장)",
)
def recompute_aggregates(current_user: User = Depends(get_current_user)):
    """[PRO-B-44] 데이터 오류 시 과거 Raw Event만으로 재집계. 항상 동일한 결과가 나오도록 순수 함수형 집계."""
    ChainManager.recompute_aggregates_from_events(current_user.id)


@router.post(
    "/events/complete",
    response_model=RecordCompletionResponse,
    summary="[PRO-B-44] 완료 이벤트 기록 (Idempotency Key, 원자적 트랜잭션)",
)
def record_completion_event(
    body: RecordCompletionRequest,
    current_user: User = Depends(get_current_user),
):
    """
    [PRO-B-44] 서버 기반 집계: Raw Event 기록 + ChainLength·일별 집계 갱신.
    동일 idempotency_key 재전송 시 멱등 처리. 완료 처리와 체인 업데이트는 원자적.
    """
    completed_at = body.completed_at or datetime.now(timezone.utc)
    result = ChainManager.record_completion(
        task_id=body.task_id,
        user_id=current_user.id,
        completed_at=completed_at,
        idempotency_key=body.idempotency_key,
    )
    return RecordCompletionResponse(
        user_id=result.user_id,
        chain_length=result.chain_length,
        is_long_term_chain=result.is_long_term_chain,
        daily_completion_count=result.daily_completion_count,
        already_processed=result.already_processed,
    )


# ── [PRO-B-42] 실시간 ChainLength·Revalidation ───────────────────────────────────

@router.get(
    "/state",
    response_model=ChainStateResponse,
    summary="[PRO-B-42] ChainLength 상태 조회 (Revalidation — 로컬 우선 후 서버 정합성)",
)
def get_chain_state(current_user: User = Depends(get_current_user)):
    """
    [PRO-B-42] Revalidation — 0.5초 이내 업데이트·종료 후 유지.
    앱 재진입 시 클라이언트는 로컬 스토리지(SharedPreferences/UserDefaults/SQLite)의
    chain_length를 먼저 표시한 뒤, 이 API로 서버와 정합성을 맞춘다.
    """
    state = _get_service().get_chain_state(current_user.id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chain state not found for user.",
        )
    return state


# ── Chain 갱신 (task_complete 시 내부 호출용; 필요 시 노출) ─────────────────────

@router.post(
    "/on-complete",
    response_model=ChainUpdateResult,
    summary="[PRO-B-41] task_complete 시 ChainLength 산출·갱신",
)
def update_chain_on_complete(
    completed_at: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
):
    """
    할 일 완료 시점에 ChainLength를 갱신한다.
    보통은 PATCH /tasks/{id} 로 status=completed 시 서버에서 내부 호출한다.
    completed_at 미지정 시 현재 시각(UTC) 사용.
    """
    when = completed_at or datetime.now(timezone.utc)
    return _get_service().update_chain_on_task_complete(current_user.id, when)


# ── [PRO-B-43] 설정 기반 스티커 등급 ────────────────────────────────────────────

@router.get(
    "/sticker-grade",
    response_model=StickerGradeResponse,
    summary="[PRO-B-43] 완료 수별 스티커 등급 조회 (getStickerGrade, id 포함 → sticker_exposed 로그용)",
)
def get_sticker_grade_for_count(
    completion_count: int,
    current_user: User = Depends(get_current_user),
):
    """
    [PRO-B-43] 설정값 기반 getStickerGrade.
    상한선·유효성 적용. 반환 id로 sticker_exposed 이벤트 로그 가능.
    """
    grade = get_sticker_grade(completion_count)
    if grade is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sticker grade not found for given completion_count.",
        )
    return StickerGradeResponse(
        id=grade.id,
        name=grade.name,
        name_ko=grade.name_ko,
        image_path=grade.image_path,
        completion_count=grade.completion_count,
    )


# ── DailyCompletion [PRO-B-43] ─────────────────────────────────────────────────

@router.get(
    "/daily-completion",
    response_model=DailyCompletionResponse,
    summary="[PRO-B-41][PRO-B-43] 날짜별 완료 수·sticker_grade 조회/갱신",
)
def get_or_update_daily(
    completion_date: date,
    completed_count: int,
    current_user: User = Depends(get_current_user),
):
    """해당 날짜의 일일 완료 수(0 ~ MaxActiveTaskCount)를 기록하고 [PRO-B-43] 설정 기반 스티커 등급(id·이미지 등)을 반환한다."""
    max_count = get_max_active_task_count()
    if not 0 <= completed_count <= max_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"completed_count must be between 0 and {max_count} (MaxActiveTaskCount).",
        )
    row = _get_service().get_or_update_daily_completion(
        current_user.id, completion_date, completed_count
    )
    resp = DailyCompletionResponse.model_validate(row)
    # [PRO-B-43] 결정된 등급 전체 반환(id 포함 → sticker_exposed 로그용)
    grade = get_sticker_grade(row.completed_count)
    resp.sticker = (
        StickerGradeResponse(
            id=grade.id,
            name=grade.name,
            name_ko=grade.name_ko,
            image_path=grade.image_path,
            completion_count=grade.completion_count,
        )
        if grade
        else None
    )
    return resp


# ── 성공 기준 검증 로깅 ───────────────────────────────────────────────────────

@router.post(
    "/analytics/calendar-view",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[PRO-B-41] 캘린더 노출 시 chain_length 로그",
)
def record_calendar_view(
    body: RecordCalendarViewRequest,
    current_user: User = Depends(get_current_user),
):
    """캘린더 화면 노출 시 calendar_view 이벤트와 현재 ChainLength를 전송한다."""
    _get_service().record_calendar_view(current_user.id, body.chain_length)


@router.post(
    "/analytics/sticker-exposed",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[PRO-B-43] sticker_exposed 이벤트 로그 (결정된 등급 id)",
)
def record_sticker_exposed(
    body: RecordStickerExposedRequest,
    current_user: User = Depends(get_current_user),
):
    """[PRO-B-43] 스티커 노출 시 등급 id를 포함해 로그한다."""
    _get_service().record_sticker_exposed(current_user.id, body.sticker_grade_id)


@router.post(
    "/analytics/app-lifecycle",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[PRO-B-41] app_paused/app_terminate 시 dwell_time_after_complete 로그",
)
def record_app_lifecycle(
    body: RecordAppLifecycleRequest,
    current_user: User = Depends(get_current_user),
):
    """
    앱 백그라운드 전환(app_paused) 또는 종료(app_terminate) 시 호출.
    task_complete ~ 해당 시점 사이의 체류 시간(ms)을 계산해 로그한다.
    """
    if body.event_type not in (ChainAnalyticsEventType.APP_PAUSED, ChainAnalyticsEventType.APP_TERMINATE):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="event_type must be app_paused or app_terminate",
        )
    _get_service().record_dwell_time_after_complete(
        current_user.id, body.event_type, body.occurred_at
    )


# ── 활성 사용자 세그먼트 ───────────────────────────────────────────────────────

@router.get(
    "/users/active",
    summary="[PRO-B-41] 활성 사용자 여부 (최근 7일 내 앱 진입/이벤트)",
)
def is_active_user(
    within_days: Optional[int] = None,
    current_user: User = Depends(get_current_user),
):
    """최근 N일 내 앱 진입(또는 이벤트) 기록이 있으면 True."""
    return {
        "user_id": current_user.id,
        "is_active": _get_service().is_active_user(current_user.id, within_days),
    }
