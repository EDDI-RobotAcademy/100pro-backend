# Focus Today Trigger

A/B 테스트 및 유저 행동 분석 시스템 — 실험군(Experimental) 전용 로직.  
ReEntryLatency·무행동(Inaction) 추적 및 개입(Intervention) 트리거.

## 기술 스택

- **Runtime**: Node.js 18+
- **Framework**: Express
- **DB**: MySQL (mysql2)
- **구조**: Controller-Service-Repository

## 설정

1. `.env.example`을 복사해 `.env` 생성 후 DB·포트 등 설정.
2. MySQL에 DB 생성 후 마이그레이션 실행:

```bash
npm run migrate
```

3. 서버 실행:

```bash
npm start
# 또는 개발 시
npm run dev
```

## 환경 변수 (요약)

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `TASK_DISPLAY_SCOPE` | [PRO-B-27] 당일/범위 | `today` |
| `INACTION_TRIGGER_SECONDS` | [PRO-B-31] 무행동 N초 초과 시 개입 | `30` |
| `HIGH_RISK_EXIT_INACTION_MS` | [PRO-B-32] 고위험 이탈 무행동 기준(ms) | `30000` |
| `EARLY_EXIT_THRESHOLD_SECONDS` | 조기 이탈 기준(초) | `60` |

## API (실험군 전용)

Base path: `/experimental`

### 세션 [PRO-B-30, PRO-B-32]

- `POST /session/app-open` — 앱 진입. Body: `{ "user_id": "..." }` → `session_id`, `app_open_at`
- `POST /session/action` — 목표 생성/체크 등 액션. Body: `{ "session_id": "...", "action_type": "goal_create"|"check"|"other" }`
- `POST /session/app-close` — 앱 종료. Body: `{ "session_id": "...", "app_close_at": "ISO8601" (optional) }`
- `GET /session/user/:user_id` — [PRO-B-27] TaskDisplayScope 적용 세션 목록 (당일 기준)

### 개입 [PRO-B-31]

- `GET|POST /intervention/state?user_id=...&session_id=...` — 개입 상태·포커스 여부 (`focus_input`: 목표 입력창 포커싱 여부)
- `POST /intervention/check` — 무행동 30초 초과 시 실험군만 개입 트리거. Body: `{ "user_id", "session_id" }`

## 디렉터리 구조

```
src/
  config/           # TaskDisplayScope, InactionTriggerSeconds 등
  db/               # MySQL 풀
  logger.js         # reentry_latency_ms, action_type 등 구조화 로깅
  experimental/     # 실험군 전용
    controllers/
    services/       # SessionService, InterventionService, ExitAnalysisService
    repositories/
    routes/
  index.js          # Express 앱
migrations/         # session_log, intervention_log DDL
```

## 테스트

```bash
npm test
```

- **SessionService**: app_open 기록, 첫 액션 시 ReEntryLatency 계산, first_action_at null 유지
- **InterventionService**: InactionTriggerSeconds 초과 감지, 실험군만 개입 발행, focus_input 반환
- **ExitAnalysisService**: pre_exit_inaction_ms, 조기 이탈(60초), is_high_risk_exit
- **experimentGroup**: 동일 user_id 동일 그룹, 대조군은 개입 없음

## 백로그 매핑

- **PRO-B-27**: TaskDisplayScope 기본값 `today`, 당일 세션 조회
- **PRO-B-30**: session_log, app_open_at / first_action_at / ReEntryLatency, 로깅
- **PRO-B-31**: 무행동 30초 초과 감지, 실험군만 개입, intervention_log, focus_input
- **PRO-B-32**: app_close, pre_exit_inaction_ms, 조기 이탈, is_high_risk_exit
