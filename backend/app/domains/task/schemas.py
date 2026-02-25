"""
Task 도메인 요청/응답 스키마.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.domains.task.models import TaskStatus


class TaskResponse(BaseModel):
    """과업 단건 응답."""

    id: int
    title: str
    description: Optional[str] = None
    status: TaskStatus
    user_id: int
    due_date: datetime
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskUpdateResponse(BaseModel):
    """
    [PRO-B-42] PATCH /tasks/{id} 응답 — 완료 시 chain_length 포함으로 0.5초 이내 UI 반영 지원.
    낙관적 업데이트 후 서버 응답으로 동일 값 수신 시 정합성 확보.
    """

    id: int
    title: str
    description: Optional[str] = None
    status: TaskStatus
    user_id: int
    due_date: datetime
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime
    # task_complete 시 서버가 갱신한 ChainLength — 한 번의 왕복으로 캘린더 UI 동기화
    chain_length: Optional[int] = None
    is_long_term_chain: Optional[bool] = None

    model_config = {"from_attributes": True}


class CumulativeMissCountResponse(BaseModel):
    """사용자별 누적 task_miss 카운트 응답."""

    user_id: str = Field(..., description="사용자 식별자")
    cumulative_miss_count: int = Field(..., description="누적 task_miss 횟수")
    cached: bool = Field(..., description="Redis 캐시 적중 여부")
    timestamp: datetime = Field(..., description="조회 시각 (ms 단위 정밀도)")


class TaskMissBatchResultResponse(BaseModel):
    """배치 실행 결과 응답."""

    transitioned_count: int = Field(..., description="task_miss로 전환된 과업 수")
    execution_time_ms: float = Field(..., description="배치 실행 소요 시간(ms)")
    timestamp: datetime = Field(..., description="배치 실행 시각")

class TaskCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    due_date: datetime
    session_id: Optional[str] = Field(None, description="[STEP 3] 액션 시 session_log first_action_at / last_action_at 갱신용")

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    is_archived: Optional[bool] = None
    session_id: Optional[str] = Field(None, description="[STEP 3] 액션 시 session_log last_action_at 갱신용")

class TaskBatchAction(BaseModel):
    task_ids: list[int]
    action: str  # 'archive' or 'delete'
