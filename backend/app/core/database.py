"""
SQLAlchemy 동기 엔진 및 세션 팩토리.
DATABASE_URL 환경 변수가 없으면 프로젝트 루트의 SQLite 파일을 기본값으로 사용한다.
"""
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

_DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "100pro.db"

# Ensure the parent directory for the SQLite database exists
_DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

Base = declarative_base()

_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def _get_url() -> str:
    return os.getenv("DATABASE_URL", f"sqlite:///{_DEFAULT_DB_PATH}")


def get_engine():
    global _engine
    if _engine is None:
        url = _get_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, echo=False, connect_args=connect_args)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _SessionLocal


def init_db() -> None:
    """모든 모델 테이블을 생성한다. 앱 시작 시 1회 호출."""
    import app.domains.auth.models  # noqa: F401
    import app.domains.task.models  # noqa: F401
    import app.domains.TodayFocus.today_focus.session_log  # noqa: F401 [PM-TF-INF-01]
    import app.infrastructure.task_archive.models  # noqa: F401
    import app.infrastructure.task_tracking.models  # noqa: F401
    import app.infrastructure.task_params.models  # noqa: F401
    import app.infrastructure.experiment_config.config  # noqa: F401
    import app.infrastructure.trigger_config.settings  # noqa: F401
    Base.metadata.create_all(bind=get_engine())
