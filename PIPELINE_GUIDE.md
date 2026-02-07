# KICE 수학 문제 자동화 파이프라인 가이드

## 전체 시스템 개요

```
  [1] PDF 수집          [2] 자동 처리           [3] 검수            [4] 발송
  ─────────────        ─────────────          ─────────────       ─────────────

  KICE 공식 사이트      Python pipeline         Notion              카카오톡
       │               (src/pipeline.py)        20개 속성 검수       채널 메시지
       ▼                    ▼                     ▼                    ▼
  ┌─────────┐         ┌─────────┐           ┌─────────┐          ┌─────────┐
  │ Google  │────────►│ PDF     │──────────►│ Notion  │─────────►│ 사용자  │
  │ Drive   │         │ 변환    │           │ 검수    │          │ 앱/웹   │
  └─────────┘         └─────────┘           └─────────┘          └─────────┘
                           │                     │
                           ▼                     ▼
                      ┌─────────┐           ┌──────────┐
                      │Supabase │◄──────────│sync_to_  │
                      │ DB      │           │notion.py │
                      └─────────┘           └──────────┘
```

---

## Step 1: 환경 준비

```bash
cd Math_KICE
pip install -r requirements.txt
copy .env.example .env    # Windows
# .env 파일 편집
```

### 필수 설정

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_DRIVE_FOLDER_ID=your-folder-id
NOTION_TOKEN=secret_your-token
NOTION_DATABASE_ID=your-db-id
```

---

## Step 2: PDF 수집

### 파일명 규칙

```
YYYY_EXAM_PROBLEM.pdf  (문제)
YYYY_EXAM_ANSWER.pdf   (정답)

예: 2026_CSAT_PROBLEM.pdf, 2026_KICE6_ANSWER.pdf
```

### 업로드 방법
- Admin 페이지(`/problem/admin`)에서 PDF 업로드 버튼 사용
- 또는 Google Drive에 업로드 후 파이프라인 실행

---

## Step 3: 파이프라인 실행

### 주요 모듈

| 모듈 | 기능 |
|------|------|
| `src/pipeline.py` | 전체 파이프라인 오케스트레이션 |
| `src/pdf_converter.py` | PDF → PNG 변환 (250 DPI) |
| `src/page_splitter.py` | 하이브리드 문항 분리 (Template + OCR) |
| `src/image_processor.py` | 이미지 크롭/리사이즈 (1600px) |
| `src/answer_parser.py` | 정답 PDF 파싱 |
| `src/supabase_storage.py` | Supabase Storage 업로드 |
| `src/supabase_service.py` | DB CRUD (문제, 힌트, 통계) |
| `src/notion_service.py` | Notion API (검수 페이지, 블록 빌더) |

### 실행 명령어

```bash
# 파이프라인 실행
python src/pipeline.py --pdf "2026_CSAT_PROBLEM.pdf" --year 2026 --exam CSAT

# 하이브리드 분리 옵션
python src/pipeline.py --pdf "경로/시험지.pdf" --year 2026 --exam CSAT --no-ocr
python src/pipeline.py --pdf "경로/시험지.pdf" --year 2026 --exam CSAT --no-hybrid

# 서버 실행
python run.py

# 통계 확인
python run.py --stats
```

### 이미지 품질

| DPI | 해상도 (A4) | 용도 |
|-----|-------------|------|
| 72 | 595x842 px | 미리보기 |
| **250** | **2924x4136 px** | **권장** |
| 300 | 3508x4960 px | 인쇄 품질 |

---

## Step 4: Notion 검수

### 4.1 Notion 동기화

```bash
python sync_to_notion.py                              # 전체
python sync_to_notion.py --year 2026                  # 연도별
python sync_to_notion.py --problem-id 2026_CSAT_Q01   # 단일 문제
python sync_to_notion.py --dry-run                    # 미리보기
python sync_to_notion.py --yes                        # 확인 없이 실행
python sync_to_notion.py --status needs_review        # 상태별
```

동기화 특징:
- Rate limiting: 문제당 1.5초 간격 (Notion API ~3 req/sec)
- Exponential backoff 자동 재시도 (최대 3회)
- Circuit breaker: 5회 연속 실패 시 자동 중단
- ETA 표시: 남은 시간 실시간 계산

### 4.2 Database 속성 (20개)

| 속성 | 타입 | 설명 |
|------|------|------|
| 문제 ID | 제목 | 2026_CSAT_Q01 |
| 연도, 문항번호, 배점, 난이도 | 숫자 | 기본 정보 |
| 시험, 상태, 과목, 단원, 정답유형 | 선택 | 분류 정보 |
| 정답, 출제의도, 풀이, 힌트1~3, 검수자 | 리치 텍스트 | 콘텐츠 |
| 원본링크, 이미지폴더 | URL | 링크 |
| 검수일 | 날짜 | 검수 완료일 |

**상태 옵션**: 검수 필요(보라) / 수정 필요(빨강) / 보류(회색) / 검수 완료(초록) / 발송 준비(파랑)

### 4.3 검수 페이지 본문

```
📋 문제 정보 (Callout: 과목/단원/배점/유형/정답)
🖼️ 문제 이미지 (이미지 블록)
📝 풀이 (토글)
💡 힌트 1단계: 개념 방향 (토글, 파란 배경)
🔑 힌트 2단계: 핵심 전환 (토글, 노란 배경)
🎯 힌트 3단계: 결정적 한 줄 (토글, 빨간 배경)
📌 출제 의도 (토글)
✅ 검수 체크리스트 (8항목)
   - 문제 이미지 확인
   - 정답/배점/정답유형 확인
   - 풀이 정확성/힌트 3단계 확인
   - 과목/단원/난이도 확인
```

### 4.4 검수 프로세스

1. Notion DB에서 "검수 필요" 문제 선택
2. 문제 정보/이미지/풀이/힌트 검토
3. 체크리스트 완료
4. 상태 → "검수 완료", 검수자/검수일 기입

---

## Step 5: 카카오톡 발송

### Admin 페이지에서 발송

1. `http://localhost:8000/problem/admin`
2. 문제 목록에서 "발송" 버튼
3. 미리보기 확인 → 발송

### 자동 스케줄러

```bash
python run.py --send-once      # 1회 발송
python run.py --send-daily     # 스케줄러 (5분 간격)
```

---

## Step 6: 에이전트 시스템 (6개)

```
Commander (총괄)
├── PipelineAgent  (PDF 처리)
├── ContentAgent   (Notion/콘텐츠)
├── OpsAgent       (통계/모니터링)
├── DevAgent       (서버/의존성/코드)
└── QAAgent        (테스트/검증)
```

```bash
python -m agents.run_agents status                    # 전체 현황
python -m agents.run_agents pipeline --year 2026      # 파이프라인
python -m agents.run_agents content validate          # 데이터 검증
python -m agents.run_agents ops stats                 # 통계
python -m agents.run_agents ops health                # 헬스체크
python -m agents.run_agents dev check-server          # 서버 상태
python -m agents.run_agents dev deps                  # 의존성
python -m agents.run_agents dev code-stats            # 코드 통계
python -m agents.run_agents qa imports                # import 검증
python -m agents.run_agents qa syntax                 # 구문 검사
python -m agents.run_agents qa full-check             # 종합 검사
```

---

## 하이브리드 분리 (Hybrid Split)

한 페이지에 여러 문제가 있는 시험지를 자동 분리:

```
[1. 템플릿 분리] → [2. OCR 검증] → [3. 수동 보정 (5%만)]
```

수능 수학 템플릿: 11페이지에 Q1~Q22 배치

---

## 트러블슈팅

| 문제 | 해결 |
|------|------|
| Notion Rate limit | 자동 exponential backoff (최대 3회) |
| 2000자 제한 | 자동 분할 (1900자 단위, 줄 경계) |
| Toggle 자식 블록 | 2단계 append (Notion API 제약) |
| Windows cp949 | `python -u sync_to_notion.py --yes` |
| 5회 연속 실패 | Circuit breaker 자동 중단 |

---

## 프로젝트 파일 구조

```
Math_KICE/
├── run.py                      # CLI 메인
├── sync_to_notion.py           # Notion 동기화 CLI
├── requirements.txt
├── .env.example
├── schema_v2.sql               # DB 스키마
│
├── src/                        # 핵심 서비스
│   ├── pipeline.py             # 파이프라인
│   ├── pdf_converter.py        # PDF → PNG
│   ├── page_splitter.py        # 문항 분리
│   ├── image_processor.py      # 이미지 처리
│   ├── answer_parser.py        # 정답 파싱
│   ├── notion_service.py       # Notion API
│   ├── supabase_service.py     # DB CRUD
│   └── supabase_storage.py     # Storage
│
├── server/                     # FastAPI 서버
│   ├── main.py                 # 진입점
│   ├── problem_routes.py       # Admin + API
│   ├── scheduler.py            # 자동 발송
│   ├── dashboard_routes.py     # 분석
│   └── static/                 # React
│
├── agents/                     # 6-에이전트
│   ├── commander.py
│   ├── pipeline_agent.py
│   ├── content_agent.py
│   ├── ops_agent.py
│   ├── dev_agent.py
│   ├── qa_agent.py
│   └── run_agents.py
│
└── docs/                       # 문서
```

---

**마지막 업데이트**: 2026-02-08
