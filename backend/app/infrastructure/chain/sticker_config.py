"""
[PRO-B-43] 설정값 기반 일별 스티커 등급 매핑 — 설정 로드 및 검증.
설정값만으로 등급 기준 변경 가능(코드 수정 없음). 상한선·유효성 처리 포함.
"""
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# [PRO-B-43] 성공 기준: 설정값 관리. 기본 설정 파일 경로(환경 변수로 override 가능)
_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config" / "sticker_grades.json"


@dataclass(frozen=True)
class StickerGradeResult:
    """
    [PRO-B-43] getStickerGrade 반환값 — sticker_exposed 이벤트 로그용 id 포함.
    """

    id: int
    name: str
    image_path: str
    completion_count: int
    name_ko: str = ""


def _get_config_path() -> Path:
    path = os.getenv("STICKER_GRADES_CONFIG_PATH", "")
    if path and os.path.isfile(path):
        return Path(path)
    return _DEFAULT_CONFIG_PATH


def _load_raw_config() -> dict[str, Any]:
    """설정 파일(JSON) 로드. 파일 없으면 빈 구조 반환."""
    path = _get_config_path()
    if not path.is_file():
        logger.warning("[PRO-B-43] sticker_grades config not found at %s", path)
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("[PRO-B-43] Failed to load sticker config: %s", e)
        return {}


def _build_grade_map(raw: dict[str, Any]) -> tuple[int, int, dict[int, StickerGradeResult], StickerGradeResult | None]:
    """
    [PRO-B-43] Data-driven: 설정에서 completion_count -> 등급 맵 생성.
    새로운 스티커 등급 추가 시 JSON만 수정하면 되며 함수 로직 수정 불필요.
    """
    max_count = raw.get("max_active_task_count", 5)
    default_id = raw.get("default_grade_id", 0)
    grades_list = raw.get("grades") or []
    by_count: dict[int, StickerGradeResult] = {}
    default_grade: StickerGradeResult | None = None
    for g in grades_list:
        c = g.get("completion_count")
        if c is None:
            continue
        try:
            count = int(c)
        except (TypeError, ValueError):
            continue
        grade = StickerGradeResult(
            id=int(g.get("id", count)),
            name=str(g.get("name", "")),
            image_path=str(g.get("image_path", "")),
            completion_count=count,
            name_ko=str(g.get("name_ko", "")),
        )
        by_count[count] = grade
        if grade.id == default_id:
            default_grade = grade
    if default_grade is None and by_count:
        default_grade = by_count.get(0) or next(iter(by_count.values()))
    return max_count, default_id, by_count, default_grade


# 모듈 로드 시 1회 빌드(캐시). 설정 변경 시 프로세스 재시작 또는 reload_sticker_config() 호출
_max_active_task_count_cached = 5
_default_grade_id_cached = 0
_grade_by_count_cached: dict[int, StickerGradeResult] = {}
_default_grade_cached: StickerGradeResult | None = None


def _ensure_loaded() -> None:
    global _max_active_task_count_cached, _default_grade_id_cached
    global _grade_by_count_cached, _default_grade_cached
    if _grade_by_count_cached:
        return
    raw = _load_raw_config()
    _max_active_task_count_cached, _default_grade_id_cached, _grade_by_count_cached, _default_grade_cached = _build_grade_map(raw)


def reload_sticker_config() -> None:
    """[PRO-B-43] 설정 리로드(관리자 변경 반영용)."""
    global _grade_by_count_cached, _default_grade_cached
    _grade_by_count_cached = {}
    _default_grade_cached = None
    _ensure_loaded()


def get_max_active_task_count() -> int:
    """[PRO-B-43] 설정값 MaxActiveTaskCount (기본 5, 설정에서 변경 가능)."""
    _ensure_loaded()
    return _max_active_task_count_cached


def get_sticker_grade(completion_count: Any) -> StickerGradeResult | None:
    """
    [PRO-B-43] 설정값 기반 일별 스티커 등급 결정 — 순수 함수형 인터페이스.
    성공 기준: 코드 수정 없이 설정값만으로 등급 기준 변경 가능(설정값 관리), 상한선 처리, 유효성 검사.

    - 중복 없는 매핑: 0 ~ MaxActiveTaskCount 에 대해 설정에 정의된 고유 등급 반환.
    - 상한선(Ceiling): completion_count >= MaxActiveTaskCount 이면 무조건 최상위 등급 반환.
    - 유효성: 음수 또는 숫자가 아닌 값 → default_grade_id(0개 완료 스티커) 반환.

    반환값에 id 포함 → sticker_exposed 이벤트 로그에 사용.
    """
    _ensure_loaded()
    # [PRO-B-43] 유효성 검사: 숫자가 아니거나 음수면 기본 등급(0개 완료 스티커)
    try:
        count = int(completion_count)
    except (TypeError, ValueError):
        return _default_grade_cached
    if count < 0:
        return _default_grade_cached
    max_count = _max_active_task_count_cached
    # [PRO-B-43] 상한선 처리(Ceiling): MaxActiveTaskCount 이상이면 최상위 등급
    if count >= max_count:
        count = max_count
    grade = _grade_by_count_cached.get(count)
    return grade if grade is not None else _default_grade_cached
