"""
[PRO-B-42] ChainLength 데이터 영속성 — DAO/리포지토리 패턴.
사용자별 ChainLength 저장·조회를 단일 쿼리로 수행하여 0.5초 이내 업데이트 및
앱 재시작 후 유지 목표를 지원한다.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.core.database import get_session_factory
from app.domains.auth.models import User
from app.infrastructure.chain.constants import LONG_TERM_CHAIN_DAYS


@dataclass
class ChainStateDto:
    """[PRO-B-42] ChainLength 상태 DTO — DB 한 건 조회 결과."""

    user_id: int
    chain_length: int
    last_task_completed_at: Optional[datetime]
    is_long_term_chain: bool


class ChainRepository:
    """
    [PRO-B-42] ChainLength 영속성 접근 객체.
    User 테이블의 current_chain_length, last_task_completed_at을 효율적으로 읽고,
    update_chain_on_task_complete에서 갱신된 값을 서버 DB에 유지한다.
    """

    @staticmethod
    def get_chain_state(user_id: int) -> Optional[ChainStateDto]:
        """
        [PRO-B-42] 사용자별 ChainLength 상태 조회 (Revalidation용).
        단일 PK 조회로 지연 최소화 — 앱 재진입 시 로컬 데이터 표시 후 서버와 정합성 맞출 때 사용.
        (성공 기준: 종료 후 유지된 데이터를 효율적으로 반환.)
        """
        session_factory = get_session_factory()
        with session_factory() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            length = user.current_chain_length or 0
            last_at = user.last_task_completed_at
            is_long = length >= LONG_TERM_CHAIN_DAYS
            return ChainStateDto(
                user_id=user.id,
                chain_length=length,
                last_task_completed_at=last_at,
                is_long_term_chain=is_long,
            )
