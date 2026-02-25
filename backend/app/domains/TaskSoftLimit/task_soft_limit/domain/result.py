"""목표 생성 흐름 결과 DTO."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GoalCreateFlowResult:
    """
    목표 생성 처리 흐름 결과 (설계서 §4).
    생성은 항상 허용되며, 가이드 노출 여부와 가이드 응답 메시지를 구분.
    (Parameter Backlog: guideExposureThreshold 6일 때 가이드 응답 반환)
    """

    guide_exposed: bool
    """과부하로 인해 guide_exposed 이벤트가 기록되었으면 True."""

    guide_message: Optional[str] = None
    """가이드 노출 시 클라이언트에 전달할 메시지. guide_exposed=True일 때만 설정."""
