# 백엔드 개발 흐름 정리

이 문서는 **가설 백로그 → 인프라/파라미터 백로그 → 구현**까지의 전체 흐름을 한 번에 볼 수 있도록 정리한 것입니다.

---

## 1. 전체 목표와 가설 (앞단 백로그)

| 백로그 | 요약 | 성공 기준(핵심) |
|--------|------|----------------|
| **PRO-B-26** | 빈 화면만 제공해도 유저의 자율적 실행력 측정 | 당일 데이터만 메인 리스트, 당혹감(즉시 이탈)이 실험군 대비 높지 않음, Day-3 유지율 유지 |
| **PRO-B-28** | 30초 망설이는 유저에게 가벼운 목표 제안 → ReEntryLatency 단축 | 실험군 ReEntryLatency 20~30% 단축, 30초 인터랙션 CTR 15%+, 거부 반응 비율·완료까지 이어지는 비중 측정 |
| **PRO-B-29** | 이탈 지점을 데이터로 측정해 해결안 입증 | app_open~첫 task_start 시간 수집, 60초 초과 구간 실행 확률 시각화, 실험군/대조군 태그로 지표 분리 |

→ **백엔드 역할**: 위 가설을 검증할 수 있도록 **세션·지연·무행동·이탈·개입**을 기록하고, **실험군만 개입**을 트리거하는 인프라 제공.

---

## 2. 인프라·파라미터 백로그 → 구현 매핑

| 구분 | 백로그 | 구현 내용 |
|------|--------|-----------|
| **파라미터** | PRO-B-27 | TaskDisplayScope 기본값 `today`, 당일 생성 데이터만 조회하는 쿼리 필터 |
| **인프라** | PRO-B-30 | session_log, app_open_at / first_action_at / ReEntryLatency(ms) 산출·저장·로깅 |
| **인프라** | PRO-B-31 | 무행동 N초(기본 30초) 감지, 실험군만 개입 트리거, intervention_log, 목표 입력창 포커싱 상태 반환 |
| **인프라** | PRO-B-32 | app_close_at, pre_exit_inaction_ms, 조기 이탈(60초), is_high_risk_exit |

---

## 3. 이벤트 흐름 (한 세션 기준)

```
[클라이언트]                    [백엔드 API]                      [DB / 로그]

1. 앱 오픈
   └─ POST /experimental/session/app-open
      body: { user_id }
      └─ SessionService.startSession()
         └─ session_log INSERT (session_id, user_id, app_open_at)
         └─ 로그: session_event 'app_open', reentry_latency_ms=null, action_type=null

2. (선택) 무행동 30초 경과 시
   └─ POST /experimental/intervention/check
      body: { user_id, session_id }
      └─ InterventionService.checkAndTriggerIntervention()
         └─ 실험군이면 intervention_log INSERT, 대조군이면 무개입
         └─ 로그: intervention_event 'triggered'

3. (선택) 개입 후 화면 상태 확인
   └─ GET /experimental/intervention/state?user_id=...&session_id=...
      └─ focus_input: true → 클라이언트가 목표 입력창 포커스

4. 유저 첫 액션 (목표 생성 / 체크)
   └─ POST /experimental/session/action
      body: { session_id, action_type: "goal_create"|"check"|"other" }
      └─ SessionService.recordFirstOrLastAction()
         └─ session_log UPDATE: first_action_at, reentry_latency_ms, action_type
         └─ 개입이 있었으면 intervention_log UPDATE: first_action_after_trigger_at
         └─ 로그: session_event 'first_action', reentry_latency_ms, action_type

5. 이후 액션들
   └─ POST /experimental/session/action (동일)
      └─ session_log UPDATE: last_action_at, action_type
      └─ intervention_log first_action_after_trigger_at 갱신(해당 시 한 번만)

6. 앱 종료
   └─ POST /experimental/session/app-close
      body: { session_id, app_close_at? }
      └─ ExitAnalysisService.closeSession()
         └─ pre_exit_inaction_ms = app_close_at - last_action_at
         └─ 조기 이탈: app_close_at - app_open_at ≤ 60초
         └─ is_high_risk_exit: pre_exit_inaction_ms ≥ 기준 또는 첫 액션 없음
         └─ session_log UPDATE
         └─ 로그: session_event 'app_close', pre_exit_inaction_ms, is_high_risk_exit
```

---

## 4. 데이터 흐름 요약

| 시점 | session_log | intervention_log | 로그에 남는 핵심 필드 |
|------|-------------|-------------------|------------------------|
| app_open | INSERT (session_id, user_id, app_open_at) | — | session_id, user_id, app_open_at |
| 30초 무행동 + 실험군 | — | INSERT (triggered_at) | experiment_group, triggered_at |
| first action | UPDATE first_action_at, reentry_latency_ms, action_type | UPDATE first_action_after_trigger_at (해당 시) | reentry_latency_ms, action_type |
| 이후 action | UPDATE last_action_at, action_type | — | action_type |
| app_close | UPDATE app_close_at, pre_exit_inaction_ms, is_high_risk_exit | — | pre_exit_inaction_ms, is_high_risk_exit, session_ended |

---

## 5. 실험군 vs 대조군

- **분기**: `user_id` 기준 해시로 동일 유저는 항상 같은 그룹 (experimental / control).
- **실험군**: 무행동 30초 초과 시 개입 트리거 발행 → intervention_log 기록, `focus_input`으로 목표 입력창 포커싱 유도.
- **대조군**: 개입 트리거 없음, intervention_log 미기록.
- **공통**: session_log·ReEntryLatency·이탈 지표는 두 그룹 모두 수집 → PRO-B-28/29 비교 분석용.

---

## 6. 파라미터로 제어되는 부분

| 파라미터 | 용도 | 기본값 |
|----------|------|--------|
| TaskDisplayScope | 메인 리스트/세션 조회 시 “당일만” 등 범위 [PRO-B-27] | `today` |
| InactionTriggerSeconds | 이 시간(초) 무행동 초과 시 개입 [PRO-B-31] | `30` |
| HighRiskExitInactionMs | 이탈 직전 무행동(ms) 이상이면 고위험 이탈 [PRO-B-32] | `30000` |
| EarlyExitThresholdSeconds | 진입 후 이 시간(초) 이내 종료면 조기 이탈 [PRO-B-32] | `60` |

---

## 7. 앞으로 이어질 수 있는 작업 (백로그 기준)

- **PRO-B-26**: “당일 생성 데이터만 메인 리스트” → 이미 TaskDisplayScope·당일 필터 구현됨. 할일(Task) 도메인 API와 연동 시 동일 필터 적용.
- **PRO-B-28**: 클라이언트 30초 타이머·인터랙션 노출/클릭 → 백엔드는 `/intervention/check`, `/intervention/state`로 개입 트리거·포커스 상태 제공 완료.
- **PRO-B-29**: re_entry_performance 이벤트 스키마, 클릭 횟수(count) 수집, 60초 이상 지연/3회 이상 클릭 세그먼트 분석 쿼리 등은 추후 확장 가능.

---

## 8. 프로젝트에서 생성·관리하는 파일

- **`.gitignore`**  
  - `node_modules/` — 의존성 제외  
  - `dist/` — 빌드 산출물 제외  
  - `.env` — DB 비밀번호 등 로컬 설정을 저장소에 올리지 않음 (참고용은 `.env.example` 사용)

이 파일은 **앞선 가설(PRO-B-26, 28, 29)과 현재 구현(PRO-B-27, 30, 31, 32)의 연결**을 한 번에 보기 위한 개발 흐름 정리입니다.
