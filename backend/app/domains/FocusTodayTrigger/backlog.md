### 가설 백로그

##### 1\.빈 화면만 제공할 때, 유저가 스스로 목표를 세우는 자율적 실행력을 측정할 수 있다.

&nbsp;\[PRO-B-26]

###### Success criteria

\- 유저가 스스로 '목표 추가' 버튼을 눌러 첫 과업을 생성하는 비율이 기준치 이상 유지

\- 가이드가 없는 상태에서 유저가 느끼는 당혹감(즉시 앱 종료)이 실험군 대비 유의미하게 높지 않아야 함

\- 빈 화면 상태에서도 기존 유저의 Day-3 유지율이 파괴되지 않고 일정 수준 유지됨

###### To-do

\[ ]  당일 생성된 데이터만 메인 리스트에 호출하는 API 쿼리 조건 설정

\[ ]  빈 화면 중앙에 '오늘의 목표를 추가해보세요'와 같은 최소한의 텍스트 가이드 배치



##### 2\.앱 진입 후 30초간 망설이는 유저에게 가벼운 목표를 제안하면, ReEntryLatency가 단축되어 실행 확률이 높아질 것이다. \[PRO-B-28]

###### Success criteria

\- 실험군의 ReEntryLatency가 대조군 대비 통계적으로 유의미하게(약 20~30%) 단축되어야 함

\- 30초 시점에 노출된 인터랙션(말 걸기)의 클릭 전환율(CTR)이 15% 이상 달성되어야 함

\- 인터랙션 노출 직후 60초 이내에 앱을 꺼버리는 '거부 반응' 비율이 대조군보다 낮거나 같아야 함

\- 인터랙션을 통해 생성된 첫 목표가 실제로 '완료(Check)'까지 이어지는 비중이 확인되어야 함

###### To-do

\[ ]  앱 진입(app\_open) 시점부터 유저 액션을 감시하는 30초 카운트다운 타이머 구현

타이머 종료 전 유저 액션(스크롤 제외 클릭 등) 발생 시 인터랙션 실행을 취소하는 인터럽트 로직 개발

\[ ]  인터랙션 클릭 시 즉시 목표 입력창이 포커싱되거나 추천 목표가 자동 입력되는 UX 흐름 설계

\[ ]  "가장 쉬운 것부터 시작해볼까요?" 등 심리적 부담을 낮추는 마이크로카피 적용

\[ ]  인터랙션의 노출 빈도 및 재노출 쿨타임(Cool-down) 파라미터 설정



##### 3\.유저의 심리적 저항이 물리적 이탈로 변하는 지점을 데이터로 측정한다면 해결안의 유효성을 입증할 수 있다.\[PRO-B-29]

###### Success criteria

\- 모든 세션에서 app\_open부터 첫 task\_start까지의 시간이 오차 없이 초 단위로 수집되어야 함 → 60초 초과 구간에서 실행 확률이 실제로 급감하는지 여부를 데이터 대시보드에서 시각화 할 수 있어야 함

\- 첫 실행 전 발생하는 클릭 횟수(탐색 효율성)와 최종 실행 여부 간의 상관 관계 도출 가능해야 함

\- A/B 테스트 그룹 별로 지표를 분리하여 볼 수 있도록 실험군/대조군 태그가 로그에 포함되어야 함(지연 시간 비교)

###### To-do

\[ ]  서버 및 클라이언트 공통으로 사용할 re\_entry\_performance 이벤트 스키마 정의

첫 액션 발생 시까지 누적되는 클릭 횟수(count)를 세션 단위로 임시 저장하고 전송하는 로직 구현

\[ ]  유저가 앱을 그냥 꺼버린 경우(app\_close)에도 마지막까지 머문 시간을 전송하는 종료 로그(exit log) 심기

\[ ]  수집된 raw 데이터를 바탕으로 '60초 이상 지연 유저'와 '3회 이상 클릭 유저'를 세그먼트화하는 분석 쿼리 작성



### 인프라 백로그

##### 1\.앱 진입 이벤트 수신 시 세션 시작 시각과 첫 액션 발생 시각을 기록하여 ReEntryLatency를 산출하는 구조를 추가한다. \[PRO-B-30]

###### Success criteria

\- 앱 진입 이벤트 수신 시점의 `user\_id`, `session\_id`, `app\_open\_at` 이 기록된다.

\- 첫 액션(목표 생성 또는 체크) 발생 시점의 `first\_action\_at` 이 사용자 단위로 기록된다.

\- `ReEntryLatency = first\_action\_at - app\_open\_at` 값이 산출되어 저장된다.

\- 첫 액션 없이 세션이 종료된 경우 `first\_action\_at = null` 로 기록되어 이탈 세션으로 분류된다.

\- 산출된 값이 로그 또는 저장소에 기록되어 사후 분석이 가능하다.

###### To-do

DB

\[ ]  `session\_log` 테이블을 정의한다.

&nbsp;   - `session\_id(PK), user\_id(FK), app\_open\_at, first\_action\_at, reentry\_latency\_ms, action\_type, created\_at`

Service

\[ ]  앱 진입 이벤트 수신 시 `app\_open\_at` 을 기록하는 로직을 추가한다.

\[ ]  첫 액션 발생 이벤트 수신 시 `first\_action\_at` 을 기록하고 `ReEntryLatency` 를 계산하는 로직을 추가한다.

\[ ]  세션 종료 시점까지 첫 액션이 없는 경우 `first\_action\_at = null` 로 저장하는 분기 구조를 추가한다.

Repository

\[ ]  `session\_log` 테이블에 진입/액션/종료 이벤트를 INSERT/UPDATE하는 쿼리를 구현한다.

\[ ]  `user\_id` + `app\_open\_at` 기준으로 세션을 조회하는 쿼리를 구현한다.

Logging

\[ ]  `session\_id`, `user\_id`, `reentry\_latency\_ms`, `action\_type`, 세션 종료 여부를 로그에 기록하는 구조를 추가한다.



##### 2\.앱 진입 후 무행동 지속 시간을 감지하여 InactionTriggerSeconds 초과 시 실험군/대조군 분기에 따라 개입 트리거 이벤트를 발행하는 구조를 추가한다. \[PRO-B-31]

###### Success criteria

\- 앱 진입 후 첫 액션 없이 경과한 시간을 서버 또는 클라이언트에서 측정할 수 있다.

\- 경과 시간이 `InactionTriggerSeconds` 를 초과하는 시점을 감지할 수 있다.

\- 사용자 단위 실험군/대조군 분기 로직이 적용된다.

\- 실험군에 한해 개입 트리거 이벤트가 발행되고, 대조군은 개입 없이 유지된다.

\- 분기 결과, 개입 발행 여부, 이후 사용자 첫 액션 발생 여부가 이벤트로 기록되어 실험 분석이 가능하다.

###### To-do

DB

\[ ]  `intervention\_log` 테이블을 정의한다.

&nbsp;   - `log\_id(PK), user\_id(FK), session\_id, experiment\_group, triggered\_at, first\_action\_after\_trigger\_at, created\_at`

Service

\[ ]  세션 내 무행동 경과 시간을 추적하고 `InactionTriggerSeconds` 초과 여부를 판단하는 로직을 추가한다.

\[ ]  사용자 단위 A/B 실험 분기 로직을 추가한다.

\[ ]  실험군 판별 시 개입 트리거 이벤트를 발행하는 분기 구조를 추가한다.

\[ ]  대조군 판별 시 개입 없이 세션을 유지하는 분기 구조를 추가한다.

Repository

\[ ]  분기 결과 및 개입 트리거 발행 여부를 `intervention\_log` 테이블에 INSERT하는 쿼리를 구현한다.

\[ ]  개입 이후 첫 액션 발생 시각을 UPDATE하는 쿼리를 구현한다.

Logging

\[ ]  `user\_id`, `session\_id`, `experiment\_group`, `triggered\_at`, `first\_action\_after\_trigger\_at` 을 로그에 기록하는 구조를 추가한다.



##### 3\.앱 진입 후 세션 종료까지의 행동 시퀀스를 기록하여 이탈 직전 무행동 구간과 app\_close 시점을 저장하는 구조를 추가한다. \[PRO-B-32]

###### Success criteria

\- 앱 진입부터 종료까지 발생한 액션 시퀀스가 사용자 단위로 기록된다.

\- 마지막 액션 발생 시각과 `app\_close\_at` 의 차이(이탈 직전 무행동 구간)를 산출할 수 있다.

\- `app\_close\_at` 이 `first\_action\_at` 으로부터 60초 이내인 세션을 분류할 수 있다.

\- 이탈 직전 무행동 구간이 기준값 이상인 세션을 고위험 이탈 세션으로 분류하여 저장할 수 있다.

\- 산출된 값이 로그 또는 저장소에 기록되어 사후 분석이 가능하다.

###### To-do

DB

\[ ]  `session\_log` 테이블에 `last\_action\_at`, `app\_close\_at`, `pre\_exit\_inaction\_ms`, `is\_high\_risk\_exit` 컬럼을 추가한다.

Service

\[ ]  세션 내 마지막 액션 발생 시각을 갱신하는 로직을 추가한다.

\[ ]  `app\_close` 이벤트 수신 시 `app\_close\_at` 을 기록하고 `pre\_exit\_inaction\_ms = app\_close\_at - last\_action\_at` 을 계산하는 로직을 추가한다.

\- \[ ]  `app\_close\_at - app\_open\_at ≤ 60s` 조건을 만족하는 세션을 조기 이탈 세션으로 분류하는 로직을 추가한다.

\[ ]  `pre\_exit\_inaction\_ms` 가 기준값 이상인 세션을 `is\_high\_risk\_exit = true` 로 저장하는 분기 구조를 추가한다.

Repository

\[ ]  `app\_close` 이벤트 수신 시 `session\_log` 테이블의 해당 레코드를 UPDATE하는 쿼리를 구현한다.

\[ ]  `is\_high\_risk\_exit = true` 기준으로 세션을 조회하는 쿼리를 구현한다.

Logging

\[ ]  `session\_id`, `user\_id`, `last\_action\_at`, `app\_close\_at`, `pre\_exit\_inaction\_ms`, `is\_high\_risk\_exit` 를 로그에 기록하는 구조를 추가한다.



### 파라미터 백로그

##### 1\.오늘 날짜 기준 표시 범위(TaskDisplayScope) 기본값을 today로 설정 \[PRO-B-27]

###### Success criteria

\- TaskDisplayScope는 설정값으로 관리된다.

\- TaskDisplayScope의 기본값은 today(당일 기준 할일만 표시)로 설정된다.

\- 설정값 변경 시 코드 수정 없이 정책이 반영된다.

\- 변경된 TaskDisplayScope 값은 즉시 홈 화면 할일 조회 로직에 반영된다.

###### To-do

\[ ]  TaskDisplayScope 설정 파라미터 정의

\[ ]  기본값을 today로 설정

\[ ]  설정값 로딩 구조 구현

\[ ]  설정 변경 반영 테스트 (값 변경 시 조회 범위 즉시 변경 확인)

