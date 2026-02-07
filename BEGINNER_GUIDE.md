# 수학 문제 자동화 시스템 - 초보자 가이드

이 가이드는 프로그래밍 경험이 없어도 따라할 수 있도록 기초부터 설명합니다.

---

## 목차
1. [전체 시스템 이해하기](#1-전체-시스템-이해하기)
2. [Python 환경 설정](#2-python-환경-설정)
3. [Google Drive 설정](#3-google-drive-설정)
4. [Notion 설정](#4-notion-설정)
5. [Supabase 설정](#5-supabase-설정)
6. [KakaoTalk 설정](#6-kakaotalk-설정)
7. [시스템 실행하기](#7-시스템-실행하기)
8. [문제 해결](#8-문제-해결)

---

## 1. 전체 시스템 이해하기

### 시스템 흐름

```
[1] PDF 수집          [2] 이미지 변환         [3] 검수
Google Drive    →    PyMuPDF (250 DPI)   →   Notion (20개 속성)
                           ↓                    ↓
[6] 발송             [5] 저장              [4] 동기화
KakaoTalk       ←    Supabase DB     ←    sync_to_notion.py
```

### 시스템 구성

| 구성 요소 | 역할 | 비용 |
|----------|------|------|
| **Python + FastAPI** | 자동화 핵심 엔진 + 웹서버 | 무료 |
| **Google Drive** | PDF 파일 저장소 | 무료 (15GB) |
| **Notion** | 문제 검수 및 관리 (20개 속성, 풍부한 페이지) | 무료 |
| **Supabase** | 데이터베이스 + 이미지 저장소 | 무료 (500MB) |
| **KakaoTalk API** | 문제 이미지 발송 | 무료 |

---

## 2. Python 환경 설정

### 2.1 Python 설치하기

1. https://www.python.org/downloads/ 접속
2. `Download Python 3.11.x` 버튼 클릭
3. **중요!** `Add Python to PATH` 체크 후 `Install Now`

```bash
python --version  # Python 3.11.x 표시되면 성공
```

### 2.2 프로젝트 설정

```bash
cd Math_KICE

# 가상 환경 (권장)
python -m venv venv
venv\Scripts\activate    # Windows

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
copy .env.example .env    # Windows
# .env 파일 편집하여 API 키 입력
```

### 2.3 필요한 라이브러리

| 라이브러리 | 용도 |
|-----------|------|
| `fastapi` + `uvicorn` | 웹 서버 |
| `google-api-python-client` | Google Drive 연동 |
| `PyMuPDF` | PDF → PNG 변환 |
| `notion-client` | Notion API 연동 |
| `supabase` | Supabase 데이터베이스 |
| `python-dotenv` | 환경 변수 관리 |
| `Pillow` | 이미지 처리 |

---

## 3. Google Drive 설정

### 3.1 Google Cloud 프로젝트 생성

1. https://console.cloud.google.com 접속
2. 상단 프로젝트 드롭다운 → `새 프로젝트` → 이름: `KICE-Math`
3. `API 및 서비스` → `라이브러리` → `Google Drive API` 활성화

### 3.2 OAuth 설정

1. `OAuth 동의 화면` → `External` → 앱 이름: `KICE Math`
2. 범위 추가: `drive.readonly`, `drive.file`
3. `사용자 인증 정보` → `OAuth 클라이언트 ID` → `데스크톱 앱`
4. `.env`에 입력:
   ```
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

### 3.3 Drive 폴더

1. Google Drive에서 `KICE_Math` 폴더 생성
2. URL에서 폴더 ID 복사 → `.env`의 `GOOGLE_DRIVE_FOLDER_ID`

### 3.4 PDF 파일 이름 규칙

| 시험 | 문제 파일명 | 정답 파일명 |
|------|-------------|-------------|
| 2026 수능 | 2026_CSAT_PROBLEM.pdf | 2026_CSAT_ANSWER.pdf |
| 2026 6월 모의 | 2026_KICE6_PROBLEM.pdf | 2026_KICE6_ANSWER.pdf |
| 2026 9월 모의 | 2026_KICE9_PROBLEM.pdf | 2026_KICE9_ANSWER.pdf |

---

## 4. Notion 설정

### 4.1 Integration 만들기

1. https://www.notion.so/my-integrations → `+ 새 통합 만들기`
2. 이름: `KICE Math` → `Internal` → `제출`
3. 토큰 복사 → `.env`의 `NOTION_TOKEN`

### 4.2 데이터베이스 만들기

1. Notion에서 `+ 페이지 추가` → `수학 문제 관리`
2. `/database` → `데이터베이스 - 전체 페이지`
3. 오른쪽 상단 `···` → `연결` → `KICE Math` 선택 **(필수!)**
4. URL에서 DB ID 복사 → `.env`의 `NOTION_DATABASE_ID`

### 4.3 데이터베이스 속성 (20개)

`sync_to_notion.py` 실행 시 자동 생성됩니다:

| 속성명 | 타입 | 설명 |
|--------|------|------|
| **문제 ID** | 제목 | 2026_CSAT_Q01 |
| **연도** | 숫자 | 2024, 2025, 2026 |
| **시험** | 선택 | CSAT, KICE6, KICE9 |
| **문항번호** | 숫자 | 1~30 |
| **배점** | 숫자 | 2, 3, 4 |
| **상태** | 선택 | 검수 필요 / 수정 필요 / 보류 / 검수 완료 / 발송 준비 |
| **과목** | 선택 | Math1, Math2 |
| **단원** | 선택 | 지수로그, 삼각함수, 수열, 미분, 적분 등 |
| **정답** | 리치 텍스트 | 정답 값 |
| **출제의도** | 리치 텍스트 | 출제 의도 |
| **풀이** | 리치 텍스트 | 풀이 (2000자 제한) |
| **힌트1~3** | 리치 텍스트 | 3단계 힌트 |
| **난이도** | 숫자 | 1~5 |
| **정답유형** | 선택 | 객관식/주관식 |
| **검수자** | 리치 텍스트 | 검수자 이름 |
| **검수일** | 날짜 | 검수 완료일 |
| **원본링크** | URL | 이미지 URL |
| **이미지폴더** | URL | 폴더 링크 |

### 4.4 검수 페이지 본문

각 문제별 Notion 페이지에 자동 생성:

```
📋 문제 정보 (과목/단원/배점/유형/정답)
🖼️ 문제 이미지
📝 풀이 (토글)
💡 힌트 1단계 (토글, 파란 배경)
🔑 힌트 2단계 (토글, 노란 배경)
🎯 힌트 3단계 (토글, 빨간 배경)
📌 출제 의도 (토글)
✅ 검수 체크리스트 (8개 항목)
```

---

## 5. Supabase 설정

1. https://supabase.com → GitHub 로그인 → New Project: `kice-math` (Seoul)
2. SQL Editor에서 `schema_v2.sql` 실행
3. Project Settings → API에서 키 복사:
   - **Project URL** → `SUPABASE_URL`
   - **anon public key** → `SUPABASE_KEY`

---

## 6. KakaoTalk 설정

1. https://developers.kakao.com → 앱 생성: `KICE Math`
2. 플랫폼: `http://localhost:8000`
3. 카카오 로그인 활성화 → Redirect URI: `http://localhost:8000/auth/kakao/callback`
4. 동의항목: `talk_message` 필수

```env
KAKAO_REST_API_KEY=your-rest-api-key
KAKAO_REDIRECT_URI=http://localhost:8000/auth/kakao/callback
```

---

## 7. 시스템 실행하기

### 7.1 서버 실행

```bash
python run.py
# → http://localhost:8000
```

### 7.2 Admin 페이지

`http://localhost:8000/problem/admin`
- 문제 목록/필터, PDF 업로드, 이미지 크롭, 발송
- 연도별 검수 진행률 바
- 이미지 썸네일 미리보기

### 7.3 Notion 동기화

```bash
python sync_to_notion.py                              # 전체 동기화
python sync_to_notion.py --year 2026                  # 연도별
python sync_to_notion.py --problem-id 2026_CSAT_Q01   # 단일 문제
python sync_to_notion.py --dry-run                    # 미리보기
python sync_to_notion.py --yes                        # 확인 없이 실행
```

### 7.4 에이전트 시스템

```bash
python -m agents.run_agents status                    # 전체 현황
python -m agents.run_agents pipeline --year 2026      # 파이프라인
python -m agents.run_agents ops stats                 # 통계
python -m agents.run_agents dev code-stats            # 코드 통계
python -m agents.run_agents qa full-check             # 품질 검사
```

---

## 8. 문제 해결

| 문제 | 해결 |
|------|------|
| Google Drive 인증 실패 | `del credentials\google_token.json` 후 재실행 |
| Notion "Database not found" | DB에 Integration 연결 확인 |
| Supabase 연결 실패 | URL 형식: `https://xxx.supabase.co` |
| Windows 한글 깨짐 | `python -u sync_to_notion.py --yes` |
| 카카오 버튼 에러 | localhost에서는 버튼 자동 비활성화 |
| Notion Rate limit | 자동 재시도 (exponential backoff) |

---

## 부록: 프로젝트 구조

```
Math_KICE/
├── run.py                      # CLI 실행 스크립트
├── sync_to_notion.py           # Supabase → Notion 동기화
├── requirements.txt            # 의존성
├── .env.example                # 환경 변수 템플릿
│
├── server/                     # FastAPI 웹 서버
│   ├── main.py                 # 서버 진입점
│   ├── auth.py                 # 카카오 로그인
│   ├── problem_routes.py       # Admin UI + 문제 API
│   ├── scheduler.py            # 자동 발송 스케줄러
│   ├── dashboard_routes.py     # 분석 대시보드
│   ├── kakao_message.py        # 카카오톡 발송
│   └── static/                 # React 컴포넌트
│
├── src/                        # 핵심 서비스
│   ├── pipeline.py             # 전체 파이프라인
│   ├── pdf_converter.py        # PDF → PNG 변환
│   ├── page_splitter.py        # 하이브리드 문항 분리
│   ├── image_processor.py      # 이미지 크롭 (1600px)
│   ├── notion_service.py       # Notion API (검수 페이지)
│   ├── supabase_service.py     # DB CRUD
│   └── supabase_storage.py     # Storage 업로드
│
├── agents/                     # 6-에이전트 시스템
│   ├── commander.py            # Commander 총괄
│   ├── pipeline_agent.py       # PDF 처리
│   ├── content_agent.py        # Notion/콘텐츠
│   ├── ops_agent.py            # 통계/모니터링
│   ├── dev_agent.py            # 서버/의존성
│   ├── qa_agent.py             # 품질 검증
│   └── run_agents.py           # CLI
│
├── docs/                       # 문서
├── sql/                        # SQL 스크립트
├── schema_v2.sql               # DB 스키마
└── sample_data.sql             # 샘플 데이터
```

---

**마지막 업데이트**: 2026-02-08
