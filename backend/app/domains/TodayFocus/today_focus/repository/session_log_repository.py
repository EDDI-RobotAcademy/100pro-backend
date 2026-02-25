"""
session_log Repository [PM-TF-INF-01 STEP 2].
app_open 이벤트 시 세션 레코드 생성. experiment_group="A" 고정.
"""
from datetime import datetime

from app.core.database import get_session_factory
from app.domains.TodayFocus.today_focus.session_log import SessionLog

EXPERIMENT_GROUP_A = "A"


class SessionLogRepository:
    """session_log INSERT 전담 Repository."""

    def create_session(self, user_id: str, app_open_at: datetime) -> SessionLog:
        """[PM-TF-INF-01] 세션 1건 생성. experiment_group은 "A"로 저장."""
        session_factory = get_session_factory()
        with session_factory() as db:
            row = SessionLog(
                user_id=user_id,
                app_open_at=app_open_at,
                experiment_group=EXPERIMENT_GROUP_A,
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            db.expunge(row)
        return row