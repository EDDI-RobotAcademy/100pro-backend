"""설정: ActiveTaskCount Cap, guide exposure threshold (설계서 §6)."""

import os
from typing import Optional


def get_active_task_count_cap() -> int:
    """
    권장 활성 목표 수 상한 (가이드 문구 등에 사용).

    Returns:
        기본값 5. 환경 변수 ACTIVE_TASK_COUNT_CAP으로 override.
    """
    return _int_env("ACTIVE_TASK_COUNT_CAP", 5)


def get_guide_exposure_threshold() -> int:
    """
    이 값 이상이면 과부하로 판단하고 guide_exposed 이벤트 기록.
    (Parameter Backlog: guideExposureThreshold = 6)

    Returns:
        기본값 6. 환경 변수 GUIDE_EXPOSURE_THRESHOLD로 override.
    """
    return _int_env("GUIDE_EXPOSURE_THRESHOLD", 6)


def get_guide_message() -> str:
    """
    가이드 노출 시 클라이언트에 전달할 메시지.
    (Parameter Backlog: ActiveTaskCount Cap 5 기준 가이드 응답)

    Returns:
        "오늘 목표는 최대 {cap}개가 적절해요" 형식 문자열.
    """
    cap = get_active_task_count_cap()
    return f"오늘 목표는 최대 {cap}개가 적절해요"


def _int_env(name: str, default: int) -> int:
    value: Optional[str] = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default
