"""
Task 도메인 모델.
과업(Task)의 상태(status)와 기한(due_date)을 중심으로 정의한다.
"""
import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, Text, func

from app.core.database import Base


class TaskStatus(str, enum.Enum):
    """과업 상태 열거형."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    TASK_MISS = "task_miss"


class Task(Base):
    """과업 테이블."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        Enum(TaskStatus),
        nullable=False,
        default=TaskStatus.PENDING,
        index=True,
    )
    from sqlalchemy import ForeignKey
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    due_date = Column(DateTime, nullable=False, index=True)
    is_archived = Column(Boolean, nullable=False, default=False, index=True)  # [PRO-B-21]
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
