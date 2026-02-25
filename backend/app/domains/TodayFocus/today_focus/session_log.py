"""
session_log 모델 [PM-TF-INF-01 STEP 2, STEP 3, STEP 4].
앱 진입(app_open) 이벤트 시 세션 기록. experiment_group은 Group A 기준 "A" 저장.
STEP 3: first_action_at, reentry_latency_ms, last_action_at (첫 액션 시 계산 / 매 액션마다 갱신).
STEP 4: app_close_at, pre_exit_inaction_ms, is_high_risk_exit (app_close 시 계산).
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from app.core.database import Base


def _generate_session_id() -> str:
    """session_id 고유 식별자 생성."""
    return str(uuid.uuid4())


class SessionLog(Base):
    """[PM-TF-INF-01] 앱 세션 로그 테이블. app_open 시 1건 INSERT. 첫 액션 시 ReEntryLatency 산출."""

    __tablename__ = "session_log"

    session_id = Column(String(36), primary_key=True, default=_generate_session_id)
    user_id = Column(String(64), nullable=False, index=True)
    app_open_at = Column(DateTime, nullable=False, index=True)
    experiment_group = Column(String(8), nullable=False, default="A", index=True)
    first_action_at = Column(DateTime, nullable=True)
    reentry_latency_ms = Column(Integer, nullable=True)
    last_action_at = Column(DateTime, nullable=True)
    app_close_at = Column(DateTime, nullable=True)
    pre_exit_inaction_ms = Column(Integer, nullable=True)
    is_high_risk_exit = Column(Boolean, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
