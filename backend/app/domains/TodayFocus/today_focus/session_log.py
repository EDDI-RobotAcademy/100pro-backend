"""
session_log 모델 [PM-TF-INF-01 STEP 2].
앱 진입(app_open) 이벤트 시 세션 기록. experiment_group은 Group A 기준 "A" 저장.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, func

from app.core.database import Base


def _generate_session_id() -> str:
    """session_id 고유 식별자 생성."""
    return str(uuid.uuid4())


class SessionLog(Base):
    """[PM-TF-INF-01] 앱 세션 로그 테이블. app_open 시 1건 INSERT."""

    __tablename__ = "session_log"

    session_id = Column(String(36), primary_key=True, default=_generate_session_id)
    user_id = Column(String(64), nullable=False, index=True)
    app_open_at = Column(DateTime, nullable=False, index=True)
    experiment_group = Column(String(8), nullable=False, default="A", index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
