"""
[PRO-B-41][PRO-B-44] Chain·일일 성취 모델.
TaskCompletionEvent: [PRO-B-44] Raw Event — task_id, user_id, completed_at, Idempotency Key.
DailyCompletion: Aggregated Stats — 날짜별 완료 수(0~5) 및 sticker_grade_id.
ChainAnalyticsLog: 성공 기준 검증용 앱 이벤트 로그.
"""
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func

from app.core.database import Base


class TaskCompletionEvent(Base):
    """
    [PRO-B-44] Raw Event 테이블 — 완료 이벤트 로그.
    task_id, user_id, completed_at 기록. idempotency_key로 멱등성 보장(중복 요청 시 ChainLength 중복 증가 방지).
    """

    __tablename__ = "task_completion_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, nullable=False, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    completed_at = Column(DateTime, nullable=False, index=True)
    idempotency_key = Column(String(255), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class DailyCompletion(Base):
    """
    날짜별 완료 태스크 수 및 스티커 등급 [PRO-B-41][PRO-B-43].
    해당 날짜에 사용자가 완료한 태스크 수(0~5)를 기록하고,
    [PRO-B-43] 기준에 따른 sticker_grade_id를 저장한다.
    """

    __tablename__ = "daily_completions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date = Column(Date, nullable=False, index=True)
    completed_count = Column(Integer, nullable=False)  # 0~5
    sticker_grade_id = Column(Integer, nullable=True)  # [PRO-B-43] 기준 매핑
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_daily_completion_user_date"),)


class ChainAnalyticsLog(Base):
    """
    [PRO-B-41] 성공 기준 검증용 앱 이벤트 로그.
    calendar_view, app_paused, app_terminate 및 dwell_time_after_complete 등을 기록한다.
    """

    __tablename__ = "chain_analytics_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type = Column(String(32), nullable=False, index=True)
    event_at = Column(DateTime, nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = ({"sqlite_autoincrement": True},)
