"""TodayFocus 요청/응답 스키마 [PM-TF-INF-01]."""
from datetime import datetime

from pydantic import BaseModel, Field


class AppOpenRequest(BaseModel):
    """app_open 이벤트 요청."""

    user_id: str = Field(..., description="사용자 식별자")
    app_open_at: datetime | None = Field(None, description="앱 진입 시각. 없으면 서버 현재 시각 사용.")


class AppOpenResponse(BaseModel):
    """app_open 이벤트 응답. session_log 1건 생성 후 반환."""

    session_id: str
    user_id: str
    app_open_at: datetime
    experiment_group: str = "A"
    created_at: datetime

    model_config = {"from_attributes": True}


class ActionRequest(BaseModel):
    session_id: str


class AppCloseRequest(BaseModel):
    """app_close 이벤트 요청."""

    session_id: str = Field(..., description="세션 식별자")
    app_close_at: datetime | None = Field(None, description="앱 종료 시각. 없으면 서버 현재 시각 사용.")
