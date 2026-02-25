"""
FastAPI 애플리케이션 진입점.
시작 시 환경 변수 로드, DB 초기화, 스케줄러 시작을 수행한다.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.env import load_env

load_env()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 DB 초기화 → 스케줄러 시작. 종료 시 스케줄러·Redis 정리."""
    from app.core.database import init_db
    from app.core.redis import close_redis
    from app.infrastructure.task_miss import TaskMissScheduler

    init_db()

    from app.infrastructure.task_params.defaults import seed_defaults
    from app.infrastructure.experiment_config.defaults import seed_experiment_config
    from app.infrastructure.trigger_config.defaults import seed_trigger_config  # [PRO-B-25]
    from app.core.database import get_session_factory
    with get_session_factory()() as session:
        seed_defaults(session)
        seed_experiment_config(session)
        seed_trigger_config(session)  # [PRO-B-25]

    scheduler = TaskMissScheduler()
    scheduler.start()

    yield

    scheduler.shutdown()
    close_redis()


app = FastAPI(
    title="100pro Backend API",
    description="100pro 프로젝트 백엔드 — 과업 관리 및 인프라",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



from app.domains.auth.router import router as auth_router  # noqa: E402
from app.domains.task.router import router as task_router  # noqa: E402
from app.infrastructure.task_miss import router as task_miss_router  # noqa: E402
from app.infrastructure.task_strategy import router as task_strategy_router  # noqa: E402
from app.infrastructure.task_archive import router as task_archive_router  # noqa: E402
from app.infrastructure.task_tracking import router as task_tracking_router  # noqa: E402
from app.infrastructure.task_params import router as task_params_router  # noqa: E402
from app.infrastructure.experiment_config import router as experiment_config_router  # noqa: E402
from app.infrastructure.trigger_config import router as trigger_config_router  # noqa: E402 [PRO-B-25]
from app.domains.TodayFocus.today_focus import router as today_focus_router  # noqa: E402
from app.infrastructure.chain import router as chain_router  # noqa: E402 [PRO-B-41]

app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Auth [PRO-B-33]"],
)

app.include_router(
    task_router,
    prefix="/tasks",
    tags=["Tasks [PRO-B-36]"],
)

app.include_router(
    task_miss_router,
    prefix="/task-miss",
    tags=["task-miss [PRO-B-10]"],
)

app.include_router(
    task_strategy_router,
    prefix="/task-strategy",
    tags=["task-strategy [PRO-B-21]"],
)
app.include_router(
    today_focus_router,
    prefix="",
    tags=["TodayFocus [PRO-B-28]"],
)

app.include_router(
    task_archive_router,
    prefix="/task-archive",
    tags=["task-archive [PRO-B-23]"],
)

app.include_router(
    task_tracking_router,
    prefix="/task-tracking",
    tags=["task-tracking [PRO-B-24]"],
)

app.include_router(
    task_params_router,
    prefix="/params",
    tags=["params [PRO-B-16]"],
)

app.include_router(
    experiment_config_router,
    prefix="/experiment-config",
    tags=["experiment-config [PRO-B-22]"],
)

app.include_router(  # [PRO-B-25]
    trigger_config_router,
    prefix="/trigger-config",
    tags=["trigger-config [PRO-B-25]"],
)

app.include_router(
    chain_router,
    prefix="/chain",
    tags=["Chain [PRO-B-41]"],
)
