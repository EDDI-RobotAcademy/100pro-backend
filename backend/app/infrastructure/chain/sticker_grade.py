"""
[PRO-B-43] 일일 완료 수(completed_count) → 스티커 등급 매핑.
설정값 기반 getStickerGrade 사용. sticker_exposed 로그용 등급 id 반환.
"""
from app.infrastructure.chain.sticker_config import (
    StickerGradeResult,
    get_sticker_grade,
)


def completed_count_to_sticker_grade_id(completed_count: int) -> int | None:
    """
    [PRO-B-43] 날짜별 완료 수(0 ~ MaxActiveTaskCount)를 sticker_grade_id로 변환.
    설정 파일 기반 매핑, 상한선·유효성 처리 적용. DailyCompletion 저장용.
    """
    grade = get_sticker_grade(completed_count)
    return grade.id if grade is not None else None


def get_sticker_grade_for_count(completion_count: int) -> StickerGradeResult | None:
    """
    [PRO-B-43] 완료 수에 대한 스티커 등급 전체 반환(id 포함 → sticker_exposed 로그용).
    순수 함수형: 설정 로드 후 completion_count에 맞는 등급만 반환.
    """
    return get_sticker_grade(completion_count)
