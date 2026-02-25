"""
session_log Repository [PM-TF-INF-01 STEP 2, STEP 3, STEP 4].
app_open 이벤트 시 세션 레코드 생성. experiment_group="A" 고정.
STEP 3: 첫 액션 시 first_action_at / reentry_latency_ms 기록, 매 액션마다 last_action_at 갱신.
STEP 4: app_close 시 app_close_at, pre_exit_inaction_ms, is_high_risk_exit 기록.
"""
from datetime import datetime

from app.core.database import get_session_factory
from app.domains.TodayFocus.today_focus.session_log import SessionLog

EXPERIMENT_GROUP_A = "A"
HIGH_RISK_EXIT_THRESHOLD_MS = 30_000


class SessionLogRepository:
    """session_log INSERT/UPDATE 전담 Repository."""

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

    def get_by_session_id(self, session_id: str) -> SessionLog | None:
        """session_id로 세션 1건 조회."""
        session_factory = get_session_factory()
        with session_factory() as db:
            row = db.query(SessionLog).filter(SessionLog.session_id == session_id).first()
            if row is None:
                return None
            db.expunge(row)
        return row

    def update_on_action(self, session_id: str, action_at: datetime) -> None:
        """[PM-TF-INF-02 STEP 3] 액션 시 first_action_at(첫 액션만), reentry_latency_ms(첫 액션만), last_action_at 갱신."""
        session_factory = get_session_factory()
        with session_factory() as db:
            row = db.query(SessionLog).filter(SessionLog.session_id == session_id).first()
            if row is None:
                return
            if row.first_action_at is None:
                row.first_action_at = action_at
                delta = action_at - row.app_open_at
                row.reentry_latency_ms = max(0, int(delta.total_seconds() * 1000))
            row.last_action_at = action_at
            db.commit()

    def update_on_app_close(self, session_id: str, app_close_at: datetime) -> None:
        """[PM-TF-INF-03 STEP 4] app_close 시 app_close_at, pre_exit_inaction_ms, is_high_risk_exit 기록."""
        session_factory = get_session_factory()
        with session_factory() as db:
            row = db.query(SessionLog).filter(SessionLog.session_id == session_id).first()
            if row is None:
                return
            row.app_close_at = app_close_at
            ref_at = row.last_action_at if row.last_action_at is not None else row.app_open_at
            delta = app_close_at - ref_at
            row.pre_exit_inaction_ms = max(0, int(delta.total_seconds() * 1000))
            row.is_high_risk_exit = row.pre_exit_inaction_ms >= HIGH_RISK_EXIT_THRESHOLD_MS
            db.commit()