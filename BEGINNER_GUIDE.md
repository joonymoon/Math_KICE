# 수학 문제 자동화 시스템 - 초보자 가이드

이 가이드는 프로그래밍 경험이 없어도 따라할 수 있도록 기초부터 설명합니다.

---

## 목차
1. [전체 시스템 이해하기](#1-전체-시스템-이해하기)
2. [Python 환경 설정](#2-python-환경-설정)
3. [Google Drive 설정](#3-google-drive-설정)
4. [Notion 설정](#4-notion-설정)
5. [Supabase 설정](#5-supabase-설정)
6. [시스템 실행하기](#6-시스템-실행하기)
7. [문제 해결](#7-문제-해결)

---

## 1. 전체 시스템 이해하기

### 우리가 만들 시스템의 흐름

```
[1] PDF 수집          [2] 이미지 변환         [3] 검토
Google Drive    →    PyMuPDF (250 DPI)   →   Notion
                           ↓
[6] 발송             [5] 저장              [4] 업로드
KakaoTalk       ←    Supabase DB     ←    Supabase Storage
```

### 시스템 구성

| 구성 요소 | 역할 | 비용 |
|----------|------|------|
| **Python + FastAPI** | 자동화 핵심 엔진 + 웹서버 | 무료 |
| **Google Drive** | PDF 파일 저장소 | 무료 (15GB) |
| **Notion** | 문제 검수 및 관리 화면 | 무료 |
| **Supabase** | 데이터베이스 + 이미지 저장소 | 무료 (500MB) |
| **KakaoTalk API** | 문제 이미지 발송 | 무료 |

### Make.com 대신 Python을 사용하는 이유

- ✅ **완전 무료** - 월간 사용량 제한 없음
- ✅ **더 유연함** - 원하는 대로 커스터마이징 가능
- ✅ **로컬 실행** - 인터넷 연결 없이도 PDF 변환 가능
- ✅ **학습 가치** - 프로그래밍 기초 학습 기회

---

## 2. Python 환경 설정

### 2.1 Python 설치하기

**Step 1: Python 다운로드**
1. https://www.python.org/downloads/ 접속
2. `Download Python 3.11.x` 버튼 클릭
3. 다운로드된 파일 실행

**Step 2: 설치 옵션**
1. ⚠️ **중요!** `Add Python to PATH` 체크
2. `Install Now` 클릭
3. 설치 완료까지 대기

**Step 3: 설치 확인**
1. 명령 프롬프트(CMD) 또는 터미널 열기
2. 다음 명령어 입력:
```bash
python --version
```
3. `Python 3.11.x`가 표시되면 성공!

### 2.2 프로젝트 설정

**Step 1: 프로젝트 폴더로 이동**
```bash
cd Math_KICE
```

**Step 2: 의존성 설치**
```bash
pip install -r requirements.txt
```

**Step 3: 환경 변수 설정**
```bash
# .env.example을 .env로 복사
copy .env.example .env    # Windows
# 또는
cp .env.example .env      # Mac/Linux
```

### 2.3 필요한 라이브러리

| 라이브러리 | 용도 |
|-----------|------|
| `google-api-python-client` | Google Drive 연동 |
| `PyMuPDF` | PDF → PNG 변환 |
| `notion-client` | Notion API 연동 |
| `supabase` | Supabase 데이터베이스 |
| `python-dotenv` | 환경 변수 관리 |

---

## 3. Google Drive 설정

### 3.1 Google Cloud 프로젝트 생성

**Step 1: Google Cloud Console 접속**
1. https://console.cloud.google.com 접속
2. Google 계정으로 로그인
3. 첫 방문 시 서비스 약관 동의

**Step 2: 새 프로젝트 만들기**
1. 상단 프로젝트 드롭다운 클릭 → `새 프로젝트`
2. 프로젝트 이름: `KICE-Math` 입력
3. `만들기` 클릭
4. 프로젝트 생성 완료 후 해당 프로젝트 선택

**Step 3: Google Drive API 활성화**
1. 왼쪽 메뉴 `API 및 서비스` → `라이브러리`
2. 검색창에 `Google Drive API` 입력
3. `Google Drive API` 선택 → `사용` 버튼 클릭

### 3.2 OAuth 동의 화면 설정

**Step 1: 동의 화면 구성 시작**
1. 왼쪽 메뉴 `API 및 서비스` → `OAuth 동의 화면`
2. User Type: `External` 선택 → `만들기` 클릭

**Step 2: 앱 정보 입력**
1. 앱 이름: `KICE Math` 입력
2. 사용자 지원 이메일: 본인 Gmail 선택
3. 개발자 연락처 정보: 본인 이메일 입력
4. `저장 후 계속` 클릭

**Step 3: 범위(Scopes) 추가**
1. `범위 추가 또는 삭제` 클릭
2. 필터에서 `Google Drive API` 검색
3. 다음 범위 체크:
   - `https://www.googleapis.com/auth/drive.readonly`
   - `https://www.googleapis.com/auth/drive.file`
4. `업데이트` 클릭 → `저장 후 계속` 클릭

**Step 4: 테스트 사용자 (선택사항)**
1. 본인 이메일 추가 (테스트 모드일 경우)
2. `저장 후 계속` 클릭

### 3.3 OAuth 클라이언트 ID 생성

**Step 1: 사용자 인증 정보 생성**
1. 왼쪽 메뉴 `API 및 서비스` → `사용자 인증 정보`
2. 상단 `+ 사용자 인증 정보 만들기` → `OAuth 클라이언트 ID`

**Step 2: 클라이언트 설정**
1. 애플리케이션 유형: `데스크톱 앱` 선택
2. 이름: `KICE Math Client` 입력
3. `만들기` 클릭

**Step 3: 클라이언트 정보 저장**
1. 팝업에서 다음 정보 복사하여 `.env` 파일에 저장:
   - **클라이언트 ID** → `GOOGLE_CLIENT_ID`
   - **클라이언트 보안 비밀번호** → `GOOGLE_CLIENT_SECRET`
2. `확인` 클릭

### 3.4 Google Drive 폴더 준비

**Step 1: Google Drive 접속**
1. https://drive.google.com 접속
2. Google 계정으로 로그인

**Step 2: 폴더 만들기**
1. 왼쪽 상단 `+ 새로 만들기` 클릭
2. `폴더` 선택
3. 폴더 이름: `KICE_Math` 입력 → `만들기`

**Step 3: 폴더 ID 확인**
1. 생성된 폴더 클릭하여 들어가기
2. 브라우저 주소창에서 폴더 ID 복사:
   ```
   https://drive.google.com/drive/folders/XXXXXXXXXXXXXXXXX
                                         ↑ 이 부분이 폴더 ID
   ```
3. `.env` 파일의 `GOOGLE_DRIVE_FOLDER_ID`에 붙여넣기

### 3.5 PDF 파일 이름 규칙

**중요!** 파일 이름을 정확히 맞춰야 자동화가 작동합니다.

```
문제 PDF: YYYY_EXAM_PROBLEM.pdf
정답 PDF: YYYY_EXAM_ANSWER.pdf
```

**예시:**
| 시험 | 문제 파일명 | 정답 파일명 |
|------|-------------|-------------|
| 2024 수능 | 2024_CSAT_PROBLEM.pdf | 2024_CSAT_ANSWER.pdf |
| 2024 6월 모의 | 2024_KICE6_PROBLEM.pdf | 2024_KICE6_ANSWER.pdf |
| 2024 9월 모의 | 2024_KICE9_PROBLEM.pdf | 2024_KICE9_ANSWER.pdf |

---

## 4. Notion 설정

### 4.1 Notion 가입하기

1. https://www.notion.so 접속
2. `무료로 Notion 사용하기` 클릭
3. Google 계정 또는 이메일로 가입
4. 개인용(Personal) 선택

### 4.2 검수용 데이터베이스 만들기

**Step 1: 새 페이지 만들기**
1. 왼쪽 사이드바에서 `+ 페이지 추가` 클릭
2. 페이지 이름: `수학 문제 관리` 입력
3. 빈 페이지에서 `/database` 입력
4. `데이터베이스 - 전체 페이지` 선택

**Step 2: 속성(Property) 추가하기**

테이블 상단의 `+` 버튼을 눌러 다음 속성들을 추가:

| 속성 이름 | 타입 | 설명 |
|-----------|------|------|
| 문제 ID | 제목 (기본) | 2024_CSAT_COMMON_Q05 |
| 연도 | 숫자 | 2024 |
| 시험 | 선택 | CSAT, KICE6, KICE9 |
| 문항번호 | 숫자 | 5 |
| 배점 | 숫자 | 3 또는 4 |
| 상태 | 선택 | 검수 필요, 검수 완료, 발송 준비 |
| 원본링크 | URL | Google Drive 링크 |
| 이미지폴더 | URL | 이미지 폴더 링크 |

### 4.3 Notion API 연결

**Step 1: Internal Integration 만들기**
1. https://www.notion.so/my-integrations 접속
2. `+ 새 통합 만들기` 클릭
3. 설정:
   - 이름: `KICE Math`
   - 연결된 워크스페이스: 본인 워크스페이스 선택
   - 유형: `Internal` (기본값)
4. `제출` 클릭

**Step 2: Internal Integration Token 복사**
1. 생성된 Integration 클릭
2. `내부 통합 토큰` 복사 (형식: `secret_xxx...`)
3. `.env` 파일의 `NOTION_TOKEN`에 붙여넣기

**Step 3: 데이터베이스에 Integration 연결** (중요!)
1. `수학 문제 관리` 페이지로 돌아가기
2. 오른쪽 상단 `···` 클릭
3. `연결` 또는 `Connections` 클릭
4. `KICE Math` Integration 선택 → `확인`

**Step 4: 데이터베이스 ID 확인**
1. 데이터베이스 페이지 열기
2. 브라우저 주소창에서 ID 복사:
   ```
   https://www.notion.so/XXXXXXXXXXXXXXXX?v=...
                        ↑ 이 부분이 데이터베이스 ID
   ```
3. `.env` 파일의 `NOTION_DATABASE_ID`에 붙여넣기

---

## 5. Supabase 설정

### 5.1 가입 및 프로젝트 생성

**Step 1: 가입**
1. https://supabase.com 접속
2. `Start your project` 클릭
3. GitHub 계정으로 로그인 (GitHub 가입 필요)

**Step 2: 새 프로젝트 만들기**
1. `New Project` 클릭
2. Organization: 본인 이름 선택
3. 프로젝트 이름: `kice-math`
4. 데이터베이스 비밀번호: 안전한 비밀번호 입력 (메모해두기!)
5. Region: `Northeast Asia (Seoul)` 선택
6. `Create new project` 클릭 (약 2분 소요)

### 5.2 데이터베이스 테이블 생성

**Step 1: SQL 에디터 열기**
1. 왼쪽 메뉴에서 `SQL Editor` 클릭
2. `+ New query` 클릭

**Step 2: 스키마 실행**
1. `schema_v2.sql` 파일 내용 전체 복사
2. SQL 에디터에 붙여넣기
3. `Run` 버튼 클릭 (또는 Ctrl+Enter)
4. "Success" 메시지 확인

### 5.3 API 키 확인

**`.env` 파일에 필요한 정보:**

1. 왼쪽 메뉴 `Project Settings` (톱니바퀴)
2. `API` 탭 클릭
3. 다음 정보를 `.env`에 복사:
   - **Project URL** → `SUPABASE_URL`
   - **anon public key** → `SUPABASE_KEY`

---

## 6. KakaoTalk 설정

### 6.1 카카오 개발자 앱 생성

**Step 1: 카카오 개발자 등록**
1. https://developers.kakao.com 접속
2. 로그인 후 `내 애플리케이션` 클릭
3. `애플리케이션 추가하기` 클릭
4. 앱 이름: `KICE Math` 입력 → 저장

**Step 2: 플랫폼 등록**
1. 생성된 앱 클릭
2. `앱 설정` → `플랫폼`
3. `Web 플랫폼 등록` 클릭
4. 사이트 도메인: `http://localhost:8000` 입력

**Step 3: 카카오 로그인 설정**
1. `제품 설정` → `카카오 로그인`
2. `활성화 설정` ON
3. Redirect URI 등록: `http://localhost:8000/auth/kakao/callback`

**Step 4: 동의항목 설정**
1. `제품 설정` → `카카오 로그인` → `동의항목`
2. 필수 동의:
   - `talk_message` (카카오톡 메시지 전송)

**Step 5: API 키 확인**
1. `앱 설정` → `앱 키`
2. `.env` 파일에 입력:
   ```
   KAKAO_CLIENT_ID=여기에_REST_API_키_입력
   KAKAO_REDIRECT_URI=http://localhost:8000/auth/kakao/callback
   ```

---

## 7. 시스템 실행하기

### 7.1 설정 확인

먼저 모든 설정이 올바른지 확인:

```bash
python run.py --check
```

성공 시 출력:
```
✓ 모든 설정이 올바릅니다.
```

### 6.2 첫 실행 (Google 인증)

```bash
python run.py
```

**첫 실행 시:**
1. 브라우저가 자동으로 열림
2. Google 계정 선택
3. "이 앱은 확인되지 않았습니다" 경고 → `고급` → `계속`
4. 권한 허용
5. 브라우저에 "인증 성공" 메시지 표시
6. 토큰이 자동 저장됨 (다음부터 자동 로그인)

### 7.3 실행 명령어

```bash
# 웹 서버 실행 (KakaoTalk 연동)
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000

# PDF → 이미지 변환 (250 DPI 고해상도)
python -c "
import fitz
from pathlib import Path

pdf = fitz.open('./downloads/2026_CSAT_PROBLEM.pdf')
dpi = 250
zoom = dpi / 72

for i, page in enumerate(pdf):
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    pix.save(f'./output/page_{i+1:03d}.png')
"

# 이미지 크롭 및 최적화 (1600px)
python src/image_processor.py ./output/raw ./output/processed

# Supabase Storage 업로드
python src/supabase_storage.py

# 통계 확인
python run.py --stats

# Notion 동기화만 실행
python run.py --sync
```

### 7.4 이미지 품질 설정

**PDF 변환 시 DPI 설정 (중요!)**
| DPI | 해상도 (A4) | 용도 |
|-----|-------------|------|
| 72 | 595x842 px | 웹 미리보기 (품질 낮음) |
| 150 | 1240x1754 px | 일반 용도 |
| **250** | **2924x4136 px** | **권장 (선명)** |
| 300 | 3508x4960 px | 인쇄 품질 |

**이미지 처리 파이프라인**
```
PDF (250 DPI) → 고해상도 이미지 (2924px)
      ↓
헤더/푸터 자동 제거
      ↓
하단 공백 트림
      ↓
1600px로 리사이즈 (다운스케일 = 선명)
      ↓
Supabase Storage 업로드
```

### 6.4 실행 결과 확인

**성공적인 실행 예시:**
```
============================================
KICE 수학 문제 관리 시스템 시작
============================================

서비스 초기화 중...
Google Drive 연결 성공!
Supabase 연결 성공!
Notion 연결 성공!

새로운 파일 2개 발견!

[1/2] 처리 중...
파일 처리 시작: 2024_CSAT_PROBLEM.pdf
[1/6] 파일명 파싱...
[2/6] PDF 다운로드...
[3/6] PDF → PNG 변환...
  생성된 이미지: 8개
[4/6] 텍스트 추출...
[5/6] 이미지 업로드...
[6/6] 데이터 저장...

파일 처리 완료: 2024_CSAT_PROBLEM.pdf
```

---

## 7. 문제 해결

### Google Drive 인증 오류

**"토큰이 만료되었습니다" 오류:**
```bash
# credentials 폴더의 토큰 삭제 후 재인증
del credentials\google_token.json    # Windows
rm credentials/google_token.json     # Mac/Linux
python run.py
```

**"권한이 없습니다" 오류:**
- Google Cloud Console에서 Google Drive API가 활성화되었는지 확인
- OAuth 동의 화면에서 범위(Scope)가 추가되었는지 확인

### Notion 연결 오류

**"Database not found" 오류:**
- Notion 데이터베이스에 Integration이 연결되었는지 확인
- 데이터베이스 ID가 정확한지 확인

**404 오류:**
- NOTION_TOKEN이 올바른지 확인
- Integration이 `Internal` 타입인지 확인

### Supabase 연결 오류

**"ENOTFOUND" 오류:**
- SUPABASE_URL이 올바른 형식인지 확인
- 형식: `https://xxxxxxxx.supabase.co` (프로젝트 이름 아님!)

### PDF 변환 오류

**"fitz 모듈을 찾을 수 없습니다" 오류:**
```bash
pip install PyMuPDF
```

**이미지가 생성되지 않음:**
- PDF 파일이 손상되지 않았는지 확인
- 로컬에서 PDF가 열리는지 확인

### KakaoTalk 발송 오류

**"네트워크 연결 상태가 좋지 않습니다" 오류:**
- **원인**: 메시지 버튼에 localhost URL 사용
- **해결**: `server/kakao_message.py`에서 localhost 체크 확인
  ```python
  # 버튼 URL이 localhost면 버튼 추가하지 않음
  if button_url and "localhost" not in button_url:
      template["buttons"] = [...]
  ```

**이미지가 흐릿하게 보임:**
- **원인**: PDF를 낮은 DPI로 변환 후 업스케일
- **해결**:
  1. PDF를 250 DPI로 재변환 (2924x4136 px)
  2. 1600px로 다운스케일 (업스케일 ❌, 다운스케일 ✅)

**DB 이미지 URL 404 에러:**
- **원인**: DB의 image_url과 실제 파일명 불일치
- **해결**: 업로드 시 `{problem_id}.png` 형식 사용
  ```python
  storage.upload_image(local_path, f'{problem_id}.png')
  ```

---

## 부록: 프로젝트 구조

```
Math_KICE/
├── run.py                      # CLI 실행 스크립트
├── requirements.txt            # 의존성 목록
├── .env                        # 환경 변수 (본인 설정)
├── .env.example               # 환경 변수 템플릿
│
├── server/                     # FastAPI 웹 서버
│   ├── main.py                # 서버 진입점
│   ├── auth.py                # 카카오 로그인
│   ├── users.py               # 사용자 관리
│   ├── kakao_message.py       # 카카오톡 메시지 발송
│   ├── message_routes.py      # 메시지 API
│   └── problem_routes.py      # 문제 관리 API
│
├── src/                        # 소스 코드
│   ├── config.py              # 설정 관리
│   ├── google_drive_service.py # Google Drive API
│   ├── pdf_converter.py       # PDF → PNG 변환
│   ├── image_processor.py     # 이미지 크롭/최적화 (1600px)
│   ├── notion_service.py      # Notion API
│   ├── supabase_service.py    # Supabase DB API
│   ├── supabase_storage.py    # Supabase Storage API
│   ├── pipeline.py            # 전체 파이프라인
│   └── problem_mapper.py      # 문항-페이지 매핑
│
├── downloads/                  # PDF 다운로드 폴더
├── output/                     # 이미지 출력 폴더
│   └── 2026_CSAT_FINAL/       # 최종 처리된 이미지 (1600px)
├── credentials/                # 인증 정보 폴더
├── docs/                       # 문서
│   ├── AGENTS.md              # 에이전트 가이드
│   ├── SETUP.md               # 설정 가이드
│   └── PIPELINE.md            # 파이프라인 문서
│
├── sql/                        # SQL 스크립트
│   └── create_problems_table.sql
├── schema_v2.sql              # DB 스키마
└── sample_data.sql            # 샘플 데이터
```

---

## 다음 단계

1. ✅ 이 가이드를 따라 모든 서비스 설정 완료
2. ✅ `python run.py --check`로 설정 확인
3. ✅ `python run.py`로 첫 실행 성공
4. → `PIPELINE_GUIDE.md`로 전체 파이프라인 이해
5. → Notion에서 문제 검수 시작

**질문이 있으면:**
- 각 서비스의 공식 문서를 참고하세요
- GitHub Issues에 문의: https://github.com/joonymoon/Math_KICE/issues
