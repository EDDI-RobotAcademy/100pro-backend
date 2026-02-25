"""
[PRO-B-41] 성공 기준(Success Criteria) 수치 상수.
ChainLength·성취 지표 산출 및 검증 로직에서 사용하는 값들을 한 곳에서 관리한다.
"""
# Chain 유지 조건: 마지막 task_complete 이후 이 시간 이내에 새 완료가 있으면 Chain 유지/증가
CHAIN_WINDOW_HOURS = 48

# 성공 기준: 이 일수 이상 연속 달성 시 장기 연속( long-term chain )으로 판별
LONG_TERM_CHAIN_DAYS = 7

# 활성 사용자(Active User) 정의: 최근 N일 내 앱 진입/이벤트가 있으면 활성으로 간주
ACTIVE_USER_DAYS = 7

# [PRO-B-43] 일일 완료 수 범위 참고용. 스티커 등급 상한은 설정(sticker_grades.json max_active_task_count) 기준.
DAILY_COMPLETION_MAX = 5
DAILY_COMPLETION_MIN = 0

# 참고: dwell_time 등 60초 기준이 필요한 경우 추가
# DWELL_MIN_SECONDS = 60

# [PRO-B-42] 실시간 ChainLength 업데이트 성공 기준: task_complete 후 UI 반영 목표 지연(ms)
TARGET_UPDATE_LATENCY_MS = 500
