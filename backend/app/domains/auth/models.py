from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Null if Social Login
    name = Column(String(100), nullable=False)
    provider = Column(String(20), default="email", nullable=False) # 'email' or 'kakao'
    social_id = Column(String(255), unique=True, index=True, nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # [PRO-B-41][PRO-B-42] ChainLength 및 성취 지표: 연속 달성 일수, 마지막 완료 시점 (서버 DB 영속성·재진입 후 유지)
    current_chain_length = Column(Integer, nullable=False, default=0)
    last_task_completed_at = Column(DateTime, nullable=True)
