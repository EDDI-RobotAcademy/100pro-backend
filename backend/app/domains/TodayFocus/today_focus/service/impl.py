"""
TodayFocus Service 구현체 [PM-TF-PAR-01, PM-TF-INF-01 STEP 2].
TaskDisplayScope 설정을 읽어 Repository에 today 조건 적용.
app_open 이벤트 시 SessionLogRepository로 세션 생성(experiment_group="A").
"""
from datetime import datetime

from app.domains.TodayFocus.today_focus.repository import HomeTaskRepository, SessionLogRepository
from app.domains.TodayFocus.today_focus.service.interface import TodayFocusServiceProtocol
from app.domains.TodayFocus.today_focus.session_log import SessionLog
from app.domains.TodayFocus.today_focus.settings import TodayFocusSettings
from app.domains.task.models import Task


class TodayFocusServiceImpl(TodayFocusServiceProtocol):
    """[PM-TF-PAR-01] 홈 화면 할 일 조회 + [PM-TF-INF-01] app_open 세션 기록 구현체."""

    def __init__(self) -> None:
        self._repository = HomeTaskRepository()
        self._session_log_repository = SessionLogRepository()

    def get_home_tasks(self, user_id: str) -> list[Task]:
        """설정된 TaskDisplayScope에 따라 홈에 표시할 과업만 반환. 오늘 할 일 없으면 빈 리스트."""
        scope = TodayFocusSettings.task_display_scope()
        return self._repository.get_tasks_for_home(user_id, scope)

    def record_app_open(self, user_id: str, app_open_at: datetime) -> SessionLog:
        """[PM-TF-INF-01 STEP 2] app_open 이벤트 시 세션 생성. experiment_group은 "A"로 저장."""
        return self._session_log_repository.create_session(user_id, app_open_at)

    def record_action(self, session_id: str, action_at: datetime) -> None:
        """[PM-TF-INF-02 STEP 3] 액션 시 first_action_at(첫 액션만), reentry_latency_ms(첫 액션만), last_action_at 갱신."""
        self._session_log_repository.update_on_action(session_id, action_at)

    def record_app_close(self, session_id: str, app_close_at: datetime) -> None:
        """[PM-TF-INF-03 STEP 4] app_close 시 app_close_at, pre_exit_inaction_ms, is_high_risk_exit 기록."""
        self._session_log_repository.update_on_app_close(session_id, app_close_at)
