"""TodayFocus Service 인터페이스."""
from datetime import datetime

from app.domains.TodayFocus.today_focus.session_log import SessionLog
from app.domains.task.models import Task


class TodayFocusServiceProtocol:
    """홈 화면 할 일 조회·세션 기록 서비스 프로토콜."""

    def get_home_tasks(self, user_id: str) -> list[Task]:
        """TaskDisplayScope에 따라 홈에 표시할 과업 목록을 반환한다."""
        ...

    def record_app_open(self, user_id: str, app_open_at: datetime) -> SessionLog:
        """[PM-TF-INF-01] app_open 이벤트 수신 시 세션 생성. experiment_group="A" 저장."""
        ...
