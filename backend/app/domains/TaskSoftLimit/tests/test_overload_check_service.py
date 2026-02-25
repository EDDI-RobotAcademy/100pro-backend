"""과부하 판별 서비스 단위 테스트 (설정값 기반 threshold)."""

import pytest

from task_soft_limit.service.overload_check_service import OverloadCheckService


def test_is_overload_false_below_threshold():
    """기본 threshold(6) 미만이면 과부하 아님."""
    service = OverloadCheckService()
    assert service.is_overload(0) is False
    assert service.is_overload(5) is False


def test_is_overload_true_at_or_above_threshold():
    """기본 threshold(6) 이상이면 과부하."""
    service = OverloadCheckService()
    assert service.is_overload(6) is True
    assert service.is_overload(7) is True


def test_is_overload_uses_config_threshold(monkeypatch):
    """설정값(GUIDE_EXPOSURE_THRESHOLD)을 사용한다."""
    from task_soft_limit import settings as mod
    monkeypatch.setattr(mod, "get_guide_exposure_threshold", lambda: 5)
    service = OverloadCheckService()
    assert service.is_overload(4) is False
    assert service.is_overload(5) is True
