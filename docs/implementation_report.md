# KICE Math System - Implementation Report
**Date: 2026-02-08 (Updated)**

---

## Executive Summary

총 10단계 작업을 완료했습니다:

**1차 (기본 구축)**
1. PDF 파이프라인으로 2026 수능 문제 이미지 22개 일괄 등록
2. 52문제 정답 등록 + 156개 3단계 힌트 생성 + API 검증 완료
3. 자동 발송 스케줄러 구현 및 API 엔드포인트 연결

**2차 (후속 작업)**
4. 2025 수능 공식 정답 검증 (20/22 오답 수정)
5. 2026 Q23-Q30 선택과목 이미지 등록 → 52문제 100% 이미지 커버리지
6. Kakao 토큰 자동 갱신 + 적응형 문제 선택 스케줄러 연동
7. 분석 대시보드 (API + HTML) 구현
8. 2026 CSAT 30문제 unit/subject 분류 + 문제별 맞춤 힌트 81개 업데이트

**3차 (UI/UX 개선)**
9. 전면 UI/UX 개선: 문제뷰어(8개 이슈), 홈/대시보드(3), 어드민(2), OAuth/분석(3)

**4차 (검수 시스템)**
10. Notion 검수 시스템 (20속성 + 풍부한 블록) + Admin 대시보드 개선 + 6-에이전트 + 문서 업데이트

---

## Step 1: 문제 이미지 일괄 등록

### 실행 내용
- `src/pipeline.py`를 사용해 `2026_CSAT_PROBLEM.pdf` 처리
- 하이브리드 분리 (Template + OCR) 방식으로 Q01-Q22 자동 추출
- Supabase Storage (`problem-images-v2` 버킷)에 23개 이미지 업로드

### 버그 수정
| 파일 | 수정 내용 |
|------|----------|
| `src/supabase_storage.py` | 버킷명 `problem-images` → `problem-images-v2` |
| `src/supabase_storage.py` | DB 컬럼 `image_url` → `problem_image_url` (3곳) |
| `src/pipeline.py` | DB 컬럼 `image_url` → `problem_image_url` |

### 결과 (최종)
| 항목 | 수량 |
|------|------|
| 2025 CSAT | 22문제 (이미지 완료) |
| 2026 CSAT Q01-Q22 | 22문제 (이미지 완료) |
| 2026 CSAT Q23-Q30 | 8문제 (이미지 완료 - 후속 작업에서 등록) |
| **전체** | **52문제 (52개 이미지 = 100% 커버리지)** |

---

## Step 2: 힌트/정답 시스템

### 2-1: 정답 데이터 등록

**2026 CSAT (공식 정답표 - KICE PDF에서 추출)**
| 구분 | 문항 | 정답 필드 |
|------|------|-----------|
| 공통 객관식 | Q01-Q15 | `answer_verified` |
| 공통 주관식 | Q16-Q22 | `answer_verified` |
| 선택 확통 | Q23-Q30 | `answer_verified` |

주요 정답 (공통):
- Q01=1, Q02=4, Q03=5, Q04=3, Q05=3
- Q16=9, Q17=16, Q18=12, Q19=15
- Q20=130, Q21=65, Q22=457

**2025 CSAT (공식 정답 검증 완료)**
- KICE 공식 정답표(news1.kr 이미지)에서 22문제 전량 검증
- AI 추정 데이터에서 **20개 오답 발견** → `answer_verified` + `score_verified`로 수정
- 주요 수정: Q01(2→3), Q04(4→2), Q09(3→2), Q15(2→5), Q16(6→9) 등

### 2-2: 메타데이터 등록 (최종)

| 항목 | 2025 CSAT | 2026 CSAT |
|------|-----------|-----------|
| score (배점) | 22문제 완료 | 30문제 완료 |
| answer_verified | **22문제 완료** | 30문제 완료 |
| score_verified | **22문제 완료** | 미사용 |
| unit (단원) | 22문제 완료 | **30문제 완료** |
| subject (과목) | 22문제 완료 | **22문제 완료** (Q23-Q30은 선택과목=NULL) |

2026 CSAT 단원 분류:
| 단원 | 문항 |
|------|------|
| 지수로그 (Math1) | Q01, Q06, Q10, Q22 |
| 삼각함수 (Math1) | Q08, Q14, Q18 |
| 수열 (Math1) | Q03, Q12, Q16, Q20 |
| 함수의극한연속 (Math2) | Q04, Q21 |
| 미분 (Math2) | Q02, Q05, Q09, Q13, Q19 |
| 적분 (Math2) | Q07, Q11, Q15, Q17 |
| 확률과통계 (선택) | Q23-Q30 |

### 2-3: 힌트 생성 (개선 완료)

| 구분 | 수량 |
|------|------|
| 총 힌트 | 156개 (52문제 x 3단계) |
| Stage 1 (concept_direction) | 52개 |
| Stage 2 (key_transformation) | 52개 |
| Stage 3 (decisive_line) | 52개 |

**힌트 품질 개선** (2차 작업):
- 기존: 단원별 범용 템플릿 (모든 수열 문제에 같은 힌트)
- 개선: **문제별 맞춤 힌트 27문제(81개)** 업데이트
  - 2026 Q03-Q22: 실제 문제 내용 분석 후 구체적 풀이 방향 힌트
  - 2026 Q23-Q30: 확률과 통계 하위 주제별 맞춤 힌트
  - 예시: Q17 Stage1 "f(x)=4x^3-2x의 부정적분: F(x)=x^4-x^2+C"
  - 예시: Q08 Stage2 "sin^2+cos^2=1과 sin=-3cos를 연립: 10cos^2=1"

### 2-4: API 검증 결과

| 테스트 | 결과 |
|--------|------|
| `POST /problem/hint/1` (개념 방향) | PASS |
| `POST /problem/hint/2` (핵심 전환) | PASS |
| `POST /problem/hint/3` (결정적 한줄) | PASS |
| `POST /problem/submit` (정답) | PASS (is_correct=true) |
| `POST /problem/submit` (오답) | PASS (is_correct=false) |
| 주관식 정답 확인 (Q16=9) | PASS |

---

## Step 3: 자동 발송 스케줄링

### 구현 파일
- **`server/scheduler.py`** (신규/대폭 확장) - DailyScheduler 클래스 + FastAPI 라우터
- **`server/main.py`** (수정) - scheduler_router 등록 (`/schedule/*`)
- **`run.py`** (수정) - `--send-daily`, `--send-once` 옵션 추가

### 아키텍처

```
[run.py --send-daily]
       |
  DailyScheduler
       |
  ┌────┴────┐
  │         │
create    execute
schedules  pending
  │         │
  ▼         ▼
daily_    KakaoTalk
schedules  Message
table      API
  │         │
  ▼         ▼
problems  deliveries
table      table
```

### API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/schedule/status` | 오늘의 스케줄 현황 조회 |
| POST | `/schedule/create-daily` | 수동 일일 스케줄 생성 |
| POST | `/schedule/execute` | 대기 중인 스케줄 즉시 실행 |

### CLI 사용법
```bash
# 일일 발송 1회 실행
python run.py --send-once

# 스케줄러 데몬 (5분 간격 체크)
python run.py --send-daily

# 커스텀 간격 (10분)
python run.py --send-daily --interval 10
```

### 작동 방식 (개선 버전)
1. **토큰 자동 갱신**: 발송 전 `token_expires_at` 확인, 만료 10분 전이면 Kakao OAuth refresh 자동 실행
2. **적응형 문제 선택**: `recommend_next_problem()` SQL 함수 호출 (RPC), 실패 시 순차 선택 fallback
3. **스케줄 생성**: 활성 유저별로 추천 문제를 `daily_schedules` 테이블에 등록
4. **실행**: `scheduled_time` <= 현재시각인 대기 스케줄을 찾아 KakaoTalk 발송
5. **기록**: 발송 결과를 `deliveries` 테이블에 기록, 스케줄 상태 업데이트

---

## Step 4: 2025 CSAT 공식 정답 검증 (후속 1)

### 실행 내용
- KICE 공식 정답표 이미지(news1.kr) 다운로드 후 시각적 확인
- DB의 AI 추정 정답(answer)과 공식 정답 대조

### 결과
| 항목 | 수치 |
|------|------|
| 총 검증 문항 | 22문제 |
| 일치 (정확) | 2문제 (9%) |
| **불일치 (수정)** | **20문제 (91%)** |
| 수정 필드 | `answer_verified`, `score_verified` |

**교훈**: AI 추정 정답의 신뢰도가 매우 낮음 → 항상 공식 정답표로 검증 필수

---

## Step 5: 2026 Q23-Q30 선택과목 이미지 (후속 2)

### 실행 내용
- 2026 CSAT PDF 분석: 페이지 9-12 = 확률과 통계 (Q23-Q30)
- PyMuPDF(fitz)로 2.5x 줌 렌더링 + PIL getbbox로 자동 여백 트리밍
- 각 페이지에 2문제씩 → 8개 이미지를 Supabase Storage 업로드

### 결과
| 항목 | Before | After |
|------|--------|-------|
| 전체 이미지 보유 | 44/52 (85%) | **52/52 (100%)** |
| 2026 이미지 보유 | 22/30 (73%) | **30/30 (100%)** |

---

## Step 6: 토큰 자동 갱신 + 적응형 선택 (후속 3)

### 변경 파일: `server/scheduler.py`

#### 토큰 자동 갱신 (`refresh_token_if_needed`)
```python
def refresh_token_if_needed(self, user: Dict) -> Optional[str]:
    # 1. token_expires_at 확인
    # 2. 만료 10분 전이면 Kakao OAuth refresh API 호출
    # 3. 새 토큰으로 DB 업데이트
    # 4. 실패 시 기존 토큰 반환
```

#### 적응형 문제 선택 (`get_adaptive_problem`)
```python
def get_adaptive_problem(self, user: Dict) -> Optional[Dict]:
    # 1. recommend_next_problem() SQL 함수 호출 (RPC)
    # 2. 추천 사유(recommendation_reason) 포함
    # 3. RPC 실패 시 get_unsent_problems() fallback
```

### 스케줄러 흐름 변경
```
Before: get_unsent_problems() → 순차 선택
After:  get_adaptive_problem() → RPC 추천 → fallback 순차
        + refresh_token_if_needed() → 자동 갱신
```

---

## Step 7: 분석 대시보드 (후속 4)

### 신규 파일: `server/dashboard_routes.py`

#### 기능
- **JSON API**: `GET /analytics/api` - 전체 통계 데이터 반환
- **HTML 대시보드**: `GET /analytics` - 시각적 대시보드 페이지

#### 대시보드 통계
| 섹션 | 내용 |
|------|------|
| Summary Cards | 총 문제수, 검증 답안율, 총 힌트, 유저수, 정답률, 오늘 스케줄 |
| Problems by Year/Exam | 연도/시험별 문제 현황 (total, ready, images, verified) |
| Problems by Unit | 단원별 문제 분포 |
| User Performance | 유저별 레벨, 점수, 정답률, 연속 정답/오답 |
| Hint Usage | 단계별 힌트 사용 통계 |

#### 접근 방법
- 어드민 대시보드 (`/dashboard`)에 Analytics 버튼 추가
- 또는 직접 접속: `http://localhost:8000/analytics`

---

## Step 8: 문제 분류 + 힌트 품질 개선 (후속 5)

### 8-1: 2026 CSAT 문제 분류
- PDF 8페이지 시각 분석으로 30문제 전체 분류 완료
- `unit` (단원) + `subject` (과목) 업데이트

| 변경 전 | 변경 후 |
|---------|---------|
| 26/30 문제 unit=NULL | **0/30 문제 unit=NULL (100% 분류)** |
| Q02,Q04,Q05 subject 오류 | 모든 공통 문제 정확한 Math1/Math2 배정 |

### 8-2: 문제별 맞춤 힌트
- Service Role Key를 사용하여 RLS 우회 업데이트
- 27개 문제(Q03-Q30) × 3단계 = **81개 힌트** 맞춤 업데이트

**개선 예시**:
| 문제 | Before (범용) | After (맞춤) |
|------|--------------|-------------|
| Q03 Stage1 | "핵심 개념과 관련 공식을 떠올려보세요" | "Sigma(2ak-k)=0이면 2*Sigma(ak)=Sigma(k). 시그마의 선형성을 이용" |
| Q08 Stage3 | "계산 실수를 줄이기 위해 검산하세요" | "cos<0이므로 cos=-1/sqrt(10). sin=3*sqrt(10)/10" |
| Q17 Stage2 | "특수한 값을 대입하여 패턴을 찾아보세요" | "F(0)=4에서 C=4. F(x)=x^4-x^2+4" |

---

## 전체 시스템 현황

### DB 통계 (최종)
| 테이블 | 레코드 수 | 비고 |
|--------|----------|------|
| problems | 52 | 100% 이미지 보유, 100% 분류 완료 |
| hints | 156 | 81개 맞춤 힌트 포함 |
| users | 1 | |
| daily_schedules | 1+ | |
| deliveries | 2+ | |

### 수정된 파일 목록 (전체)

| 파일 | 변경 유형 |
|------|----------|
| `src/pipeline.py` | 버그 수정 (DB 컬럼명) |
| `src/supabase_storage.py` | 버그 수정 (버킷명, DB 컬럼명) |
| `server/scheduler.py` | **대폭 확장** - 토큰 갱신, 적응형 선택 |
| `server/dashboard_routes.py` | **신규** + 한국어화 - 분석 대시보드 API + HTML |
| `server/main.py` | 수정 - router 등록 + **한국어화 + 대시보드 콘텐츠 강화** |
| `run.py` | 수정 - --send-daily/--send-once 추가 |
| `server/problem_routes.py` | 수정 - 뷰어 fallback + **모바일 반응형 + 한국어화 + 색상 통일** |
| `server/static/problem_viewer.jsx` | **전면 개선** - 힌트 누적, Toast, 학습 피드백, 숫자키패드 등 |
| `server/auth.py` | 수정 - **즉시 리다이렉트 + 색상 통일** |
| `server/card_routes.py` | 수정 (DB 컬럼명) |
| `server/card_image_generator.py` | 수정 (해상도 1600x1600) |

---

## Step 9: UI/UX 전면 개선

### 9-1: 문제 뷰어 개선 (`server/static/problem_viewer.jsx`)

| 이슈 코드 | 개선 내용 |
|-----------|----------|
| **C2** (Critical) | 힌트 누적 표시: 이전 힌트가 사라지던 것 → 모든 이전 힌트 함께 표시 |
| **C3** (Critical) | 제출 후 힌트 유지: 답 제출 후 힌트가 숨겨지던 것 → 계속 표시 |
| **C4** (Critical) | window.close() → history.back() fallback으로 웹뷰 호환 |
| **H4** (High) | alert() → 인라인 Toast 알림 컴포넌트 교체 |
| **H5** (High) | 오답 시 학습 피드백: 풀이 표시 + 추가 힌트 보기 버튼 |
| **H6** (High) | 주관식 입력 `inputMode="numeric"` 추가 (모바일 숫자 키패드) |
| **M1** (Medium) | 줌 컨트롤: fixed → 이미지 영역 내부 absolute 배치 |
| **M2** (Medium) | 중복 난이도 태그 제거: "4점" + "난이도 상" → "4점 (상)" 하나로 통합 |
| **L3** (Low) | 결과 표시 slide-up 애니메이션 추가 |

추가 UX 개선:
- 제출 후 선택지에 정답(초록)/오답(빨강) 시각적 표시
- 뒤로가기 아이콘 X → 화살표(←)로 변경
- 줌 1:1 버튼은 확대 시에만 표시

### 9-2: 홈/대시보드 한국어화 (`server/main.py`)

| 이슈 코드 | 개선 내용 |
|-----------|----------|
| **H1** (High) | 전면 한국어화: "Login with Kakao" → "카카오 로그인", "Service Features" → "서비스 기능" 등 |
| **H2** (High) | 대시보드 콘텐츠 강화: 레벨/정답률/풀이수/연속정답 4-grid 통계 카드 |
| **H3** (High) | 색상 통일: `#667eea/#764ba2` → `#1e40af/#4f46e5` (일관된 인디고 테마) |

### 9-3: 어드민 모바일 반응형 (`server/problem_routes.py`)

| 이슈 코드 | 개선 내용 |
|-----------|----------|
| **C1** (Critical) | @media(max-width:768px) 반응형 CSS 추가 |
| - | 통계 카드 2열 그리드, 테이블 가로 스크롤 |
| - | 필터 바 세로 배치, 버튼/글자 크기 축소 |
| - | 크롭 모달 98% 너비 적응 |
| **H1** | 헤더/필터/통계 라벨 한국어화 |
| **H3** | 색상 통일: 헤더, 테이블 헤더, 버튼, 탭 등 일괄 `#4f46e5` |

### 9-4: OAuth + 분석 대시보드 (`server/auth.py`, `server/dashboard_routes.py`)

| 이슈 코드 | 개선 내용 |
|-----------|----------|
| **M6** (Medium) | OAuth 리다이렉트 3초 → 1초로 단축 |
| **M3** (Medium) | 분석 대시보드 전면 한국어화 (카드, 테이블 헤더, 섹션명) |
| **H3** | 분석 대시보드 그라디언트 색상 통일 |

---

## Step 10: Notion 검수 시스템 + Admin 대시보드 개선

### 10-1: Notion 검수 시스템 구현

**신규/수정 파일:**
- `src/notion_service.py` (대폭 확장) - `create_review_page()`, 블록 빌더 헬퍼
- `sync_to_notion.py` (신규) - Supabase → Notion 동기화 CLI

**Notion 데이터베이스 속성 (20개):**
| 카테고리 | 속성 | 타입 |
|----------|------|------|
| 식별 | 문제 ID, 연도, 시험, 문항번호 | 제목, 숫자, 선택, 숫자 |
| 정보 | 배점, 난이도, 과목, 단원, 정답유형 | 숫자, 숫자, 선택×3 |
| 콘텐츠 | 정답, 출제의도, 풀이, 힌트1~3, 검수자 | 리치 텍스트×7 |
| 링크 | 원본링크, 이미지폴더 | URL×2 |
| 상태 | 상태, 검수일 | 선택, 날짜 |

**검수 페이지 본문 블록:**
- 문제 정보 Callout (과목/단원/배점/유형/정답)
- 문제 이미지 (Supabase Storage URL)
- 풀이 토글 (2000자 자동 분할)
- 힌트 3단계 토글 (색상별 Callout: 파랑/노랑/빨강)
- 출제 의도 토글
- 검수 체크리스트 (8항목 To-do)

**동기화 특징:**
- Rate limiting: 문제당 1.5초 간격
- Exponential backoff 재시도 (최대 3회)
- Circuit breaker: 5회 연속 실패 시 자동 중단
- ETA 표시 + 실시간 진행률
- Upsert: 기존 페이지 업데이트 / 없으면 생성

**동기화 결과:**
| 항목 | 수치 |
|------|------|
| 동기화 문제수 | 66문제 |
| 생성된 Notion 페이지 | 66개 |
| 소요 시간 | 약 10분 |

### 10-2: Admin 대시보드 개선

**변경 파일:**
- `src/supabase_service.py` - `get_stats()`에 `by_year_status` 연도별 상태 통계 추가
- `server/problem_routes.py` - 진행률 바 CSS/JS + 이미지 썸네일 추가

**추가 기능:**
| 기능 | 설명 |
|------|------|
| 연도별 검수 진행률 바 | 각 연도의 needs_review/ready/sent 비율을 색상 바로 표시 |
| 이미지 썸네일 | 테이블에 40x40 썸네일, 호버 시 3배 확대 |
| 11열 테이블 | 기존 10열 + 이미지 열 추가 |

### 10-3: 6-에이전트 시스템

**신규 파일:**
- `agents/dev_agent.py` - DevAgent (서버/의존성/코드 통계)
- `agents/qa_agent.py` - QAAgent (import/구문/API 테스트)

**에이전트 구조 (6개):**
```
Commander (총괄)
├── PipelineAgent  (PDF 처리)
├── ContentAgent   (Notion/콘텐츠)
├── OpsAgent       (통계/모니터링)
├── DevAgent       (서버/의존성)
└── QAAgent        (테스트/검증)
```

### 10-4: 문서 전면 업데이트

모든 가이드/문서를 현재 시스템에 맞게 업데이트:
- BEGINNER_GUIDE.md, PIPELINE_GUIDE.md, SETUP_GUIDE.md
- docs/AGENTS.md, docs/SETUP.md, docs/PIPELINE.md, docs/통합설계.md
- notion_template.md (8속성 → 20속성)

---

## 전체 시스템 현황

### DB 통계 (최종)
| 테이블 | 레코드 수 | 비고 |
|--------|----------|------|
| problems | 66 | 100% 이미지 보유, 100% 분류 완료 |
| hints | 198 | 81개 맞춤 힌트 포함 |
| users | 1 | |
| daily_schedules | 1+ | |
| deliveries | 2+ | |

### 수정된 파일 목록 (전체)

| 파일 | 변경 유형 |
|------|----------|
| `src/pipeline.py` | 버그 수정 (DB 컬럼명) |
| `src/supabase_storage.py` | 버그 수정 (버킷명, DB 컬럼명) |
| `src/supabase_service.py` | 확장 - by_year_status 통계 |
| `src/notion_service.py` | **대폭 확장** - 검수 페이지 생성, 블록 빌더 |
| `sync_to_notion.py` | **신규** - Supabase → Notion CLI |
| `server/scheduler.py` | **대폭 확장** - 토큰 갱신, 적응형 선택 |
| `server/dashboard_routes.py` | **신규** - 분석 대시보드 |
| `server/main.py` | 수정 - router 등록, 한국어화 |
| `run.py` | 수정 - CLI 옵션 추가 |
| `server/problem_routes.py` | 수정 - 반응형, 한국어화, 진행률 바, 썸네일 |
| `server/static/problem_viewer.jsx` | **전면 개선** - 힌트 누적, Toast, 학습 피드백 |
| `server/auth.py` | 수정 - 리다이렉트, 색상 통일 |
| `agents/dev_agent.py` | **신규** - DevAgent |
| `agents/qa_agent.py` | **신규** - QAAgent |

---

## 후속 작업 (Action Items)

### 완료된 항목
- [x] 2025 CSAT 정답 검증 → 20개 수정 완료
- [x] 2026 Q23-Q30 이미지 등록 → 100% 커버리지
- [x] Kakao 토큰 자동 갱신 → scheduler.py 통합
- [x] 적응형 문제 선택 → recommend_next_problem() RPC 연동
- [x] 분석 대시보드 → /analytics 엔드포인트
- [x] 힌트 품질 개선 → 27문제 81개 맞춤 힌트
- [x] 문제 메타데이터 분류 → 30문제 unit/subject 완료
- [x] UI/UX 전면 개선 → 4개 Critical + 6개 High + 3개 Medium + 1개 Low 수정
- [x] Notion 검수 시스템 → 20속성 + 풍부한 본문 블록, 66문제 동기화
- [x] Admin 대시보드 개선 → 연도별 진행률 바 + 이미지 썸네일
- [x] 6-에이전트 시스템 → DevAgent + QAAgent 추가
- [x] 문서 전면 업데이트 → 모든 가이드/문서 현행화

### 남은 항목
1. **채널 메시지 발송**: 현재 "나에게 보내기" → 카카오톡 채널(친구) 발송 확장
2. **난이도 자동 계산**: 정답률 기반 difficulty_auto 필드 업데이트
3. **도메인 및 SSL**: 프로덕션 배포 준비
4. **Supabase RLS**: Row Level Security 설정
