"""
[PRO-B-41] Chain·일일 성취 서비스 인터페이스.
ChainLength 산출, DailyCompletion 관리, 성공 기준 검증용 로깅 계약을 정의한다.
"""
from datetime import date, datetime
from typing import Protocol

from app.infrastructure.chain.models import DailyCompletion
from app.infrastructure.chain.schemas import ChainStateResponse, ChainUpdateResult


class ChainService(Protocol):
    """ChainLength 및 성취 지표 서비스 인터페이스 [PRO-B-41][PRO-B-42]."""

    def get_chain_state(self, user_id: int) -> ChainStateResponse | None:
        """[PRO-B-42] 앱 재진입 시 로컬 우선 표시 후 서버와 재검증(Revalidation)용 상태 조회."""
        ...

    def update_chain_on_task_complete(
        self, user_id: int, completed_at: datetime
    ) -> ChainUpdateResult:
        """task_complete 시점에 ChainLength를 산출·갱신하고, 7일 이상 여부를 반환한다."""
        ...

    def get_or_update_daily_completion(
        self, user_id: int, completion_date: date, completed_count: int
    ) -> DailyCompletion:
        """해당 날짜의 일일 완료 수를 기록하고 [PRO-B-43] sticker_grade_id를 매핑한다."""
        ...

    def record_calendar_view(self, user_id: int, chain_length: int) -> None:
        """캘린더 노출 시 calendar_view 이벤트와 현재 ChainLength를 로그한다."""
        ...

    def record_dwell_time_after_complete(
        self, user_id: int, event_type: str, occurred_at: datetime | None
    ) -> None:
        """task_complete ~ app_paused/terminate 구간(Δt, ms)을 계산해 로그한다."""
        ...

    def record_sticker_exposed(
        self, user_id: int, sticker_grade_id: int, metadata: dict | None = None
    ) -> None:
        """[PRO-B-43] sticker_exposed 이벤트 로그(결정된 등급 id 포함)."""
        ...

    def is_active_user(self, user_id: int, within_days: int | None = None) -> bool:
        """최근 N일 내 앱 진입(또는 이벤트) 기록이 있으면 활성 사용자로 판별한다."""
        ...
