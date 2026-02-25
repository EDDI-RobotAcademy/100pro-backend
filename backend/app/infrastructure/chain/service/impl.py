"""
[PRO-B-41] Chain·일일 성취 서비스 구현체.
ChainLength 산출(48h 유지/초기화), DailyCompletion·sticker_grade, 성공 기준 검증 로깅.
"""
import json
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.database import get_session_factory
from app.domains.auth.models import User
from app.infrastructure.chain.constants import (
    ACTIVE_USER_DAYS,
    CHAIN_WINDOW_HOURS,
    LONG_TERM_CHAIN_DAYS,
)
from app.infrastructure.chain.models import ChainAnalyticsLog, DailyCompletion
from app.infrastructure.chain.repository import ChainRepository, ChainStateDto
from app.infrastructure.chain.schemas import (
    ChainAnalyticsEventType,
    ChainStateResponse,
    ChainUpdateResult,
)
from app.infrastructure.chain.sticker_grade import completed_count_to_sticker_grade_id

logger = logging.getLogger(__name__)


class ChainServiceImpl:
    """ChainLength 및 성취 지표 서비스 구현 [PRO-B-41][PRO-B-42]."""

    # [PRO-B-42] 0.5초 이내 업데이트·종료 후 유지: Repository 단일 조회로 지연 최소화
    def get_chain_state(self, user_id: int) -> ChainStateResponse | None:
        """
        [PRO-B-42] Revalidation용 ChainLength 상태 조회.
        앱 재시작 후 로컬 데이터를 먼저 보여주고, 이 API로 서버와 정합성을 맞춘다.
        """
        dto = ChainRepository.get_chain_state(user_id)
        if dto is None:
            return None
        return ChainStateResponse(
            user_id=dto.user_id,
            chain_length=dto.chain_length,
            last_task_completed_at=dto.last_task_completed_at,
            is_long_term_chain=dto.is_long_term_chain,
        )

    def update_chain_on_task_complete(
        self, user_id: int, completed_at: datetime
    ) -> ChainUpdateResult:
        """
        [PRO-B-42] 성공 기준: 0.5초 이내 업데이트·종료 후 유지.
        연속 달성(Chain) 유지 조건 및 7일 이상 도달 여부.
        - 마지막 task_complete로부터 48시간 이내 새 완료 → Chain 유지 또는 +1.
        - 48시간 경과 시 ChainLength 0으로 리셋(Break).
        """
        if completed_at.tzinfo is None:
            completed_at = completed_at.replace(tzinfo=timezone.utc)
        session_factory = get_session_factory()
        with session_factory() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning("[PRO-B-41] update_chain_on_task_complete: user_id=%s not found", user_id)
                return ChainUpdateResult(
                    user_id=user_id,
                    chain_length=0,
                    is_long_term_chain=False,
                    previous_chain_length=0,
                )
            previous_chain = user.current_chain_length or 0
            last_at = user.last_task_completed_at
            if last_at and last_at.tzinfo is None:
                last_at = last_at.replace(tzinfo=timezone.utc)

            window = timedelta(hours=CHAIN_WINDOW_HOURS)
            if last_at is None or (completed_at - last_at) > window:
                # Break: 48시간 초과 또는 첫 완료 → 1부터 시작
                new_chain = 1
            else:
                # 유지 또는 +1: 다른 날이면 연속 일수 +1, 같은 날이면 유지
                last_date = last_at.date() if last_at else None
                comp_date = completed_at.date()
                if last_date is not None and comp_date > last_date:
                    new_chain = previous_chain + 1
                else:
                    new_chain = previous_chain

            user.current_chain_length = new_chain
            user.last_task_completed_at = completed_at
            session.commit()
            session.refresh(user)
            is_long = new_chain >= LONG_TERM_CHAIN_DAYS
            logger.info(
                "[PRO-B-41] Chain 갱신 user_id=%s previous=%s new=%s is_long_term=%s",
                user_id, previous_chain, new_chain, is_long,
            )
            return ChainUpdateResult(
                user_id=user_id,
                chain_length=new_chain,
                is_long_term_chain=is_long,
                previous_chain_length=previous_chain,
            )

    def get_or_update_daily_completion(
        self, user_id: int, completion_date: date, completed_count: int
    ) -> DailyCompletion:
        """
        성공 기준 검증: 날짜별 완료 수(0~5) 기록 및 [PRO-B-43] sticker_grade_id 매핑.
        """
        session_factory = get_session_factory()
        with session_factory() as session:
            row = (
                session.query(DailyCompletion)
                .filter(
                    DailyCompletion.user_id == user_id,
                    DailyCompletion.date == completion_date,
                )
                .first()
            )
            sticker_id = completed_count_to_sticker_grade_id(completed_count)
            if row:
                row.completed_count = completed_count
                row.sticker_grade_id = sticker_id
                session.commit()
                session.refresh(row)
                session.expunge(row)
                return row
            row = DailyCompletion(
                user_id=user_id,
                date=completion_date,
                completed_count=completed_count,
                sticker_grade_id=sticker_id,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            session.expunge(row)
            return row

    def record_calendar_view(self, user_id: int, chain_length: int) -> None:
        """
        성공 기준 검증: 캘린더 시각화 노출 시 ChainLength를 파라미터로 전송하는 로그.
        """
        now = datetime.now(timezone.utc)
        meta = {"chain_length": chain_length}
        session_factory = get_session_factory()
        with session_factory() as session:
            log = ChainAnalyticsLog(
                user_id=user_id,
                event_type=ChainAnalyticsEventType.CALENDAR_VIEW,
                event_at=now,
                metadata_json=json.dumps(meta, ensure_ascii=False),
            )
            session.add(log)
            session.commit()
        logger.info(
            "[PRO-B-41] calendar_view user_id=%s chain_length=%s",
            user_id, chain_length,
        )

    def record_dwell_time_after_complete(
        self, user_id: int, event_type: str, occurred_at: datetime | None
    ) -> None:
        """
        성공 기준 검증: task_complete 시점 ~ app_paused/app_terminate 시점 간
        체류 시간(dwell_time_after_complete)을 밀리초로 계산해 로그 전송.
        """
        now = datetime.now(timezone.utc)
        occurred = occurred_at if occurred_at else now
        if occurred.tzinfo is None:
            occurred = occurred.replace(tzinfo=timezone.utc)
        session_factory = get_session_factory()
        with session_factory() as session:
            user = session.query(User).filter(User.id == user_id).first()
            dwell_ms = None
            if user and user.last_task_completed_at:
                last = user.last_task_completed_at
                if last.tzinfo is None:
                    last = last.replace(tzinfo=timezone.utc)
                delta = occurred - last
                dwell_ms = int(delta.total_seconds() * 1000)
            meta = {"dwell_time_ms": dwell_ms}
            log = ChainAnalyticsLog(
                user_id=user_id,
                event_type=event_type,
                event_at=occurred,
                metadata_json=json.dumps(meta, ensure_ascii=False),
            )
            session.add(log)
            session.commit()
        logger.info(
            "[PRO-B-41] dwell_time_after_complete user_id=%s event=%s dwell_ms=%s",
            user_id, event_type, dwell_ms,
        )

    def record_sticker_exposed(
        self, user_id: int, sticker_grade_id: int, metadata: dict | None = None
    ) -> None:
        """
        [PRO-B-43] sticker_exposed 이벤트 로그 — 결정된 등급 id를 포함하여 기록.
        """
        now = datetime.now(timezone.utc)
        meta = {"sticker_grade_id": sticker_grade_id}
        if metadata:
            meta.update(metadata)
        session_factory = get_session_factory()
        with session_factory() as session:
            log = ChainAnalyticsLog(
                user_id=user_id,
                event_type=ChainAnalyticsEventType.STICKER_EXPOSED,
                event_at=now,
                metadata_json=json.dumps(meta, ensure_ascii=False),
            )
            session.add(log)
            session.commit()
        logger.info("[PRO-B-43] sticker_exposed user_id=%s sticker_grade_id=%s", user_id, sticker_grade_id)

    def is_active_user(self, user_id: int, within_days: int | None = None) -> bool:
        """
        성공 기준: 활성 사용자(Active User) 세그먼트 — 최근 N일 내 앱 진입/이벤트 기록 여부.
        """
        days = within_days if within_days is not None else ACTIVE_USER_DAYS
        since = datetime.now(timezone.utc) - timedelta(days=days)
        session_factory = get_session_factory()
        with session_factory() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user and user.last_task_completed_at:
                last = user.last_task_completed_at
                if last.tzinfo is None:
                    last = last.replace(tzinfo=timezone.utc)
                if last >= since:
                    return True
            exists = (
                session.query(ChainAnalyticsLog.id)
                .filter(
                    ChainAnalyticsLog.user_id == user_id,
                    ChainAnalyticsLog.event_at >= since,
                )
                .limit(1)
                .first()
            )
            return exists is not None
