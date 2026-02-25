"""
[PRO-B-41] Chain·일일 성취 요청/응답 스키마.
"""
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Analytics 이벤트 타입 ───────────────────────────────────────

class ChainAnalyticsEventType:
    """성공 기준 검증용 앱 이벤트 타입 [PRO-B-41][PRO-B-43]."""

    CALENDAR_VIEW = "calendar_view"
    APP_PAUSED = "app_paused"
    APP_TERMINATE = "app_terminate"
    APP_ENTER = "app_enter"
    STICKER_EXPOSED = "sticker_exposed"


# ── 요청 ────────────────────────────────────────────────────────

class RecordCalendarViewRequest(BaseModel):
    """캘린더 노출 로그 기록 요청 [PRO-B-41]: calendar_view 이벤트 + 현재 ChainLength."""

    chain_length: int = Field(..., ge=0, description="현재 연속 달성 일수(ChainLength)")


class RecordAppLifecycleRequest(BaseModel):
    """앱 백그라운드/종료 시 dwell_time_after_complete 기록 요청 [PRO-B-41]."""

    event_type: str = Field(..., description="app_paused | app_terminate")
    occurred_at: Optional[datetime] = Field(None, description="이벤트 발생 시점 (없으면 서버 현재 시각)")


class RecordStickerExposedRequest(BaseModel):
    """[PRO-B-43] sticker_exposed 이벤트 기록 요청 — 결정된 등급 id 포함."""

    sticker_grade_id: int = Field(..., ge=0, description="등급 ID (getStickerGrade 반환값.id)")


class RecordCompletionRequest(BaseModel):
    """[PRO-B-44] 완료 이벤트 기록 요청 — Idempotency Key로 중복 방지."""

    task_id: int = Field(..., description="완료한 과업 ID")
    completed_at: Optional[datetime] = Field(None, description="완료 시각 (없으면 서버 현재 시각)")
    idempotency_key: str = Field(..., min_length=1, description="멱등성 키 (중복 요청 시 동일 키)")


# ── 응답 ────────────────────────────────────────────────────────

class ChainUpdateResult(BaseModel):
    """task_complete 시 ChainLength 갱신 결과 [PRO-B-41]."""

    user_id: int
    chain_length: int = Field(..., description="갱신된 연속 달성 일수")
    is_long_term_chain: bool = Field(..., description="7일 이상 연속 달성 여부(성공 기준)")
    previous_chain_length: int = 0


class StickerGradeResponse(BaseModel):
    """[PRO-B-43] 스티커 등급 응답 — sticker_exposed 로그용 id 포함."""

    id: int = Field(..., description="등급 ID (sticker_exposed 이벤트 로그에 사용)")
    name: str = ""
    name_ko: str = ""
    image_path: str = ""
    completion_count: int = 0


class DailyCompletionResponse(BaseModel):
    """날짜별 완료 기록 응답 [PRO-B-41][PRO-B-43]."""

    id: int
    user_id: int
    date: date
    completed_count: int
    sticker_grade_id: Optional[int] = None
    sticker: Optional["StickerGradeResponse"] = Field(None, description="[PRO-B-43] 결정된 등급(id·이미지 등)")

    model_config = {"from_attributes": True}


class CalendarDayEntry(BaseModel):
    """[PRO-B-44] 기간 조회 — 날짜별 완료 수·스티커 등급 ID."""

    date: str = Field(..., description="YYYY-MM-DD")
    completed_count: int = Field(..., ge=0)
    sticker_grade_id: Optional[int] = None


class CalendarMonthResponse(BaseModel):
    """[PRO-B-44] GET /calendar — 특정 달(Month) 기록 배열."""

    year: int
    month: int
    days: list[CalendarDayEntry] = Field(default_factory=list)


class RecordCompletionResponse(BaseModel):
    """[PRO-B-44] 완료 기록 응답 — 동기화용 최신 집계 포함."""

    user_id: int
    chain_length: int
    is_long_term_chain: bool
    daily_completion_count: int
    already_processed: bool = False


class ChainStateResponse(BaseModel):
    """
    [PRO-B-42] ChainLength 상태 응답 — 앱 재진입 시 로컬 우선 표시 후 서버와 재검증(Revalidation)용.
    종료 후 유지된 데이터를 한 번에 조회한다.
    """

    user_id: int
    chain_length: int = Field(..., description="연속 달성 일수 (User.current_chain_length)")
    last_task_completed_at: Optional[datetime] = Field(
        None, description="마지막 할 일 완료 시각 (영속성 검증용)"
    )
    is_long_term_chain: bool = Field(
        False, description="7일 이상 연속 달성 여부"
    )
