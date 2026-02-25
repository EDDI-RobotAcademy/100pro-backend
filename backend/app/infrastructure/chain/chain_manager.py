"""
[PRO-B-44] 서버 기반 일별 완료 집계·ChainLength 갱신 — ChainManager.
Raw Event 기록, 48h 윈도우, 일별 집계, 멱등성(Idempotency Key), 원자적 트랜잭션, 기간 조회·재집계.
"""
import calendar
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func as sqlfunc
from sqlalchemy.exc import IntegrityError

from app.core.database import get_session_factory
from app.domains.auth.models import User
from app.infrastructure.chain.constants import CHAIN_WINDOW_HOURS, LONG_TERM_CHAIN_DAYS
from app.infrastructure.chain.models import DailyCompletion, TaskCompletionEvent
from app.infrastructure.chain.sticker_grade import completed_count_to_sticker_grade_id
from app.infrastructure.chain.sticker_config import get_max_active_task_count

logger = logging.getLogger(__name__)


@dataclass
class RecordCompletionResult:
    """[PRO-B-44] record_completion 반환 — 멱등 시 기존 상태, 신규 시 갱신 결과."""

    user_id: int
    chain_length: int
    is_long_term_chain: bool
    daily_completion_count: int
    already_processed: bool = False


@dataclass
class DayEntry:
    """[PRO-B-44] 기간 조회 API — 날짜별 완료 수·스티커 등급."""

    date: str  # YYYY-MM-DD
    completed_count: int
    sticker_grade_id: int | None


class ChainManager:
    """
    [PRO-B-44] 서버 기반 ChainLength·일별 집계 관리.
    성공 기준: 서버 기반 갱신, 멱등성(Idempotency Key), 기간 조회, 원자적 트랜잭션.
    """

    # [PRO-B-44] 48시간 윈도우 체크: 마지막 완료로부터 48h 이내면 유지/증가, 아니면 리셋
    @staticmethod
    def _compute_new_chain(
        previous_chain: int,
        last_completed_at: datetime | None,
        completed_at: datetime,
    ) -> int:
        if completed_at.tzinfo is None:
            completed_at = completed_at.replace(tzinfo=timezone.utc)
        if last_completed_at and last_completed_at.tzinfo is None:
            last_completed_at = last_completed_at.replace(tzinfo=timezone.utc)
        window = timedelta(hours=CHAIN_WINDOW_HOURS)
        if last_completed_at is None or (completed_at - last_completed_at) > window:
            return 1
        last_date = last_completed_at.date()
        comp_date = completed_at.date()
        if comp_date > last_date:
            return previous_chain + 1
        return previous_chain

    # [PRO-B-44] 일별/목표별 집계: 특정 사용자·날짜의 완료 이벤트 수 합산 (0~MaxActiveTaskCount 상한)
    @staticmethod
    def _count_daily_completions(session, user_id: int, d: date) -> int:
        start = datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        count = (
            session.query(sqlfunc.count(TaskCompletionEvent.id))
            .filter(
                TaskCompletionEvent.user_id == user_id,
                TaskCompletionEvent.completed_at >= start,
                TaskCompletionEvent.completed_at < end,
            )
            .scalar()
            or 0
        )
        cap = get_max_active_task_count()
        return min(int(count), cap)

    # [PRO-B-44] 동기화: 클라이언트 요청 시 서버 최신 집계 반환
    @staticmethod
    def record_completion(
        task_id: int,
        user_id: int,
        completed_at: datetime,
        idempotency_key: str,
    ) -> RecordCompletionResult:
        """
        [PRO-B-44] 완료 이벤트 기록 + ChainLength·일별 집계 갱신 (원자적 트랜잭션).
        Idempotency Key 중복 시 ChainLength 중복 증가 없이 기존 상태 반환.
        """
        if completed_at.tzinfo is None:
            completed_at = completed_at.replace(tzinfo=timezone.utc)
        session_factory = get_session_factory()
        with session_factory() as session:
            # [PRO-B-44] 멱등성: 이미 처리된 키면 갱신 없이 현재 집계만 반환
            existing = (
                session.query(TaskCompletionEvent)
                .filter(TaskCompletionEvent.idempotency_key == idempotency_key)
                .first()
            )
            if existing:
                # [PRO-B-44] 멱등: 이미 처리됐으면 현재 집계만 반환(별도 세션에서 조회)
                session.rollback()
                with session_factory() as read_session:
                    user = read_session.query(User).filter(User.id == user_id).first()
                    chain = (user.current_chain_length or 0) if user else 0
                    comp_date = completed_at.date()
                    dc = (
                        read_session.query(DailyCompletion)
                        .filter(
                            DailyCompletion.user_id == user_id,
                            DailyCompletion.date == comp_date,
                        )
                        .first()
                    )
                    daily_count = dc.completed_count if dc else 0
                return RecordCompletionResult(
                    user_id=user_id,
                    chain_length=chain,
                    is_long_term_chain=chain >= LONG_TERM_CHAIN_DAYS,
                    daily_completion_count=daily_count,
                    already_processed=True,
                )
            try:
                event = TaskCompletionEvent(
                    task_id=task_id,
                    user_id=user_id,
                    completed_at=completed_at,
                    idempotency_key=idempotency_key,
                )
                session.add(event)
                session.flush()
            except IntegrityError:
                session.rollback()
                return ChainManager.record_completion(
                    task_id, user_id, completed_at, idempotency_key
                )

            # [PRO-B-44] 48시간 윈도우 체크 후 ChainLength 갱신
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                session.rollback()
                return RecordCompletionResult(
                    user_id=user_id,
                    chain_length=0,
                    is_long_term_chain=False,
                    daily_completion_count=0,
                )
            prev_chain = user.current_chain_length or 0
            new_chain = ChainManager._compute_new_chain(
                prev_chain, user.last_task_completed_at, completed_at
            )
            user.current_chain_length = new_chain
            user.last_task_completed_at = completed_at

            # [PRO-B-44] 일별 집계: 해당 날짜 완료 수 갱신 (0~5)
            comp_date = completed_at.date()
            daily_count = ChainManager._count_daily_completions(session, user_id, comp_date)
            sticker_id = completed_count_to_sticker_grade_id(daily_count)
            dc = (
                session.query(DailyCompletion)
                .filter(
                    DailyCompletion.user_id == user_id,
                    DailyCompletion.date == comp_date,
                )
                .first()
            )
            if dc:
                dc.completed_count = daily_count
                dc.sticker_grade_id = sticker_id
            else:
                session.add(
                    DailyCompletion(
                        user_id=user_id,
                        date=comp_date,
                        completed_count=daily_count,
                        sticker_grade_id=sticker_id,
                    )
                )
            session.commit()
            logger.info(
                "[PRO-B-44] completion recorded task_id=%s user_id=%s chain=%s daily=%s",
                task_id, user_id, new_chain, daily_count,
            )
            return RecordCompletionResult(
                user_id=user_id,
                chain_length=new_chain,
                is_long_term_chain=(new_chain >= LONG_TERM_CHAIN_DAYS),
                daily_completion_count=daily_count,
                already_processed=False,
            )

    # [PRO-B-44] 기간 조회 API: 특정 달(Month) 날짜별 완료 수·스티커 등급 배열
    @staticmethod
    def get_month_calendar(user_id: int, year: int, month: int) -> list[DayEntry]:
        """[PRO-B-44] GET /calendar?year=&month= — 날짜별 completed_count, sticker_grade_id 배열."""
        session_factory = get_session_factory()
        with session_factory() as session:
            first_day = date(year, month, 1)
            _, last_day_num = calendar.monthrange(year, month)
            last_day = date(year, month, last_day_num)
            rows = (
                session.query(DailyCompletion)
                .filter(
                    DailyCompletion.user_id == user_id,
                    DailyCompletion.date >= first_day,
                    DailyCompletion.date <= last_day,
                )
                .all()
            )
            by_date = {r.date: (r.completed_count, r.sticker_grade_id) for r in rows}
            result = []
            for d in range(1, last_day_num + 1):
                dt = date(year, month, d)
                count, sid = by_date.get(dt, (0, None))
                result.append(
                    DayEntry(
                        date=dt.isoformat(),
                        completed_count=count,
                        sticker_grade_id=sid,
                    )
                )
            return result

    # [PRO-B-44] 재집계(Re-aggregation): Raw Event만으로 항상 동일한 결과가 나오는 순수 함수형 집계
    @staticmethod
    def recompute_aggregates_from_events(user_id: int) -> None:
        """
        [PRO-B-44] 과거 데이터 재집계. Raw Event(TaskCompletionEvent)만 읽어
        일별 완료 수·ChainLength를 다시 계산하여 Aggregated Stats에 반영.
        성공 기준: 동일 입력 → 동일 결과(순수 함수형 집계).
        """
        session_factory = get_session_factory()
        with session_factory() as session:
            events = (
                session.query(TaskCompletionEvent)
                .filter(TaskCompletionEvent.user_id == user_id)
                .order_by(TaskCompletionEvent.completed_at.asc())
                .all()
            )
            # 일별 완료 수 (순수 집계)
            daily_counts: dict[date, int] = defaultdict(int)
            cap = get_max_active_task_count()
            for e in events:
                at = e.completed_at
                if at.tzinfo is None:
                    at = at.replace(tzinfo=timezone.utc)
                d = at.date()
                daily_counts[d] = min(daily_counts[d] + 1, cap)
            # Chain: 48h 윈도우 순차 적용
            chain = 0
            last_at: datetime | None = None
            for e in events:
                at = e.completed_at
                if at.tzinfo is None:
                    at = at.replace(tzinfo=timezone.utc)
                chain = ChainManager._compute_new_chain(chain, last_at, at)
                last_at = at
            # Aggregated Stats 갱신
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.current_chain_length = chain
                user.last_task_completed_at = last_at
            for d, count in daily_counts.items():
                sticker_id = completed_count_to_sticker_grade_id(count)
                dc = (
                    session.query(DailyCompletion)
                    .filter(
                        DailyCompletion.user_id == user_id,
                        DailyCompletion.date == d,
                    )
                    .first()
                )
                if dc:
                    dc.completed_count = count
                    dc.sticker_grade_id = sticker_id
                else:
                    session.add(
                        DailyCompletion(
                            user_id=user_id,
                            date=d,
                            completed_count=count,
                            sticker_grade_id=sticker_id,
                        )
                    )
            session.commit()
            logger.info("[PRO-B-44] recompute_aggregates user_id=%s days=%s chain=%s", user_id, len(daily_counts), chain)
