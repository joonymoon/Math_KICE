# KICE 수학 문제 자동화 파이프라인 가이드

## 전체 시스템 개요

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              전체 파이프라인 흐름                                    │
└─────────────────────────────────────────────────────────────────────────────────────┘

  [1] PDF 수집          [2] 자동 처리           [3] 검수            [4] 발송
  ─────────────        ─────────────          ─────────────       ─────────────

  KICE 공식 사이트      Python 스크립트         Notion              카카오톡
       │               (run.py)               검수 대시보드         채널 메시지
       │                    │                     │                    │
       ▼                    ▼                     ▼                    ▼
  ┌─────────┐         ┌─────────┐           ┌─────────┐          ┌─────────┐
  │ Google  │────────►│ PDF     │──────────►│ 사람    │─────────►│ 사용자  │
  │ Drive   │         │ 변환    │           │ 검수    │          │ 앱/웹   │
  └─────────┘         └─────────┘           └─────────┘          └─────────┘
       │                    │                     │                    │
       │                    ▼                     ▼                    │
       │              ┌─────────┐           ┌─────────┐                │
       └─────────────►│Supabase │◄──────────│ Sync    │                │
                      │ DB      │           │         │◄───────────────┘
                      └─────────┘           └─────────┘
```

---

## Step 1: 환경 준비

### 1.1 필수 계정 가입

| 순서 | 서비스 | URL | 용도 |
|------|--------|-----|------|
| 1 | Supabase | https://supabase.com | DB + Storage |
| 2 | Google Drive | https://drive.google.com | PDF 저장소 |
| 3 | Google Cloud | https://console.cloud.google.com | API 인증 |
| 4 | Notion | https://notion.so | 검수 대시보드 |
| 5 | 카카오 개발자 | https://developers.kakao.com | 메시지 발송 |

### 1.2 Python 환경 설정

```bash
# 1. 프로젝트 폴더로 이동
cd Math_KICE

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경 변수 설정
copy .env.example .env    # Windows
cp .env.example .env      # Mac/Linux

# 4. .env 파일 편집하여 API 키 입력
```

### 1.3 Supabase 설정

1. 프로젝트 생성 (Region: Seoul)
2. SQL Editor에서 `schema_v2.sql` 실행
3. API 키 복사 → `.env` 파일

```bash
# .env 파일에 입력
SUPABASE_URL=https://xxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJI...
```

### 1.4 Google Drive 폴더 구조

```
/KICE_Math/
├── 2022/
│   ├── CSAT/
│   ├── KICE6/
│   └── KICE9/
├── 2023/
│   └── ...
├── 2024/
│   └── ...
└── 2025/
    └── ...
```

---

## Step 2: PDF 수집 (수동)

### 2.1 KICE 공식 사이트에서 다운로드

- 수능: https://www.suneung.re.kr/
- 6월/9월 모의평가: https://www.kice.re.kr/

### 2.2 파일명 규칙 (중요!)

```
형식: YYYY_EXAM_PAPER.pdf

예시:
- 2024_CSAT_PROBLEM.pdf    (수능 문제)
- 2024_CSAT_ANSWER.pdf     (수능 정답)
- 2024_KICE6_PROBLEM.pdf   (6월 모평 문제)
- 2024_KICE6_ANSWER.pdf    (6월 모평 정답)
- 2024_KICE9_PROBLEM.pdf   (9월 모평 문제)
- 2024_KICE9_ANSWER.pdf    (9월 모평 정답)
```

### 2.3 업로드

해당 폴더에 PDF 업로드 후 `python run.py` 실행

---

## Step 3: Python 워크플로우 이해

### 3.1 전체 워크플로우 (`src/workflow.py`)

```
┌────────────────────────────────────────────────────────────────────┐
│                         KICEWorkflow 클래스                         │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  [1] Google Drive        파일 목록 조회, 새 파일 감지               │
│         │                                                          │
│         ▼                                                          │
│  [2] 파일 다운로드       PDF를 로컬에 저장                          │
│         │                                                          │
│         ▼                                                          │
│  [3] PDF 변환           PyMuPDF로 PNG 이미지 생성                   │
│         │                                                          │
│         ▼                                                          │
│  [4] 텍스트 추출        PDF에서 텍스트 추출                         │
│         │                                                          │
│         ▼                                                          │
│  [5] 메타데이터 파싱    파일명에서 연도/시험 정보 추출              │
│         │                                                          │
│         ▼                                                          │
│  [6] Supabase 저장      problems 테이블에 데이터 저장               │
│         │                                                          │
│         ▼                                                          │
│  [7] Notion 카드 생성   검수용 카드 자동 생성                       │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 3.2 각 모듈 설명

#### `src/google_drive_service.py`
```python
# 주요 기능
- OAuth 인증 및 토큰 관리
- 폴더 내 파일 목록 조회
- PDF 파일 다운로드
- 이미지 파일 업로드
```

#### `src/pdf_converter.py`
```python
# 주요 기능
- PDF → PNG 변환 (PyMuPDF 사용)
- PDF 텍스트 추출
- 파일명 파싱 (연도, 시험 유형 추출)
```

#### `src/notion_service.py`
```python
# 주요 기능
- 검수 카드 생성
- 상태 업데이트
- 검수 완료 문제 조회
- Supabase 동기화
```

#### `src/supabase_service.py`
```python
# 주요 기능
- 문제 데이터 CRUD
- 힌트 관리
- 처리 이력 관리
- 통계 조회
```

### 3.3 실행 명령어

```bash
# 한 번 실행 (새 파일 처리)
python run.py

# 스케줄러 모드 (30분마다 자동 실행)
python run.py --scheduler

# 스케줄러 간격 변경 (60분마다)
python run.py --scheduler --interval 60

# 로컬 PDF 파일 처리 (Google Drive 없이)
python run.py --local "경로/파일.pdf"

# 통계 확인
python run.py --stats

# Notion 동기화만 실행
python run.py --sync

# 설정 확인
python run.py --check
```

---

## Step 4: Notion 검수 대시보드

### 4.1 Database 구조

| 속성 | 타입 | 설명 |
|------|------|------|
| 문제 ID | 제목 | 고유 식별자 (예: 2024_CSAT) |
| 연도 | 숫자 | 시험 연도 |
| 시험 | 선택 | CSAT, KICE6, KICE9 |
| 문항번호 | 숫자 | 문제 번호 |
| 배점 | 숫자 | 3 또는 4 |
| 상태 | 선택 | 검수 필요, 검수 완료, 발송 준비 |
| 원본링크 | URL | Google Drive PDF 링크 |
| 이미지폴더 | URL | 변환된 이미지 폴더 |

### 4.2 검수 프로세스

```
┌─────────────────────────────────────────────────────────────────┐
│  Notion "검수 필요" 보드에서 카드 클릭                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. 자동 추출 확인                                               │
│     - 추출된 텍스트 확인                                         │
│     - 이미지 폴더 링크 클릭하여 이미지 확인                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. 분류 확정                                                    │
│     - 과목: Math1 / Math2                                       │
│     - 단원: 세부 단원 선택                                       │
│     - 배점: 3점 / 4점                                           │
│     - 정답: 정답 입력                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. 출제의도 & 힌트 작성                                         │
│     - 출제의도: 이 문제의 핵심 개념                              │
│     - 힌트 1: 개념 방향                                         │
│     - 힌트 2: 핵심 전환                                         │
│     - 힌트 3: 결정적 한 줄                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. 완료                                                         │
│     - 상태 → "검수 완료"                                        │
│     - python run.py --sync 실행 → Supabase 자동 동기화          │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 힌트 작성 가이드

| 단계 | 이름 | 역할 | 예시 |
|------|------|------|------|
| Hint 1 | 개념 방향 | 어떤 개념/공식 사용? | "로그의 기본 성질을 활용하는 문제입니다." |
| Hint 2 | 핵심 전환 | 어떻게 변환/해석? | "log a = x로 치환하면 일차방정식이 됩니다." |
| Hint 3 | 결정적 한 줄 | 정답으로 가는 열쇠 | "x를 구한 후 10^x를 계산하세요." |

---

## Step 5: 카카오톡 발송 설정

### 5.1 카카오 개발자 설정

1. https://developers.kakao.com 로그인
2. 애플리케이션 생성
3. 플랫폼 등록 (Web)
4. 카카오 로그인 활성화
5. 동의항목: `talk_message` 필수

### 5.2 카카오톡 채널 개설

1. https://center-pf.kakao.com
2. 채널 생성
3. 카카오 개발자 앱과 연결

### 5.3 발송 테스트

```python
# main.py의 기존 코드 사용
python main.py
```

---

## Step 6: 자동 실행 설정 (선택)

### 6.1 Windows 작업 스케줄러

1. `작업 스케줄러` 열기
2. `기본 작업 만들기` 클릭
3. 트리거: 매일 오전 7시
4. 동작: `python run.py` 실행

### 6.2 Mac/Linux Cron

```bash
# crontab 편집
crontab -e

# 매일 오전 7시 실행
0 7 * * * cd /path/to/Math_KICE && python run.py
```

### 6.3 스케줄러 모드 사용

```bash
# 백그라운드에서 30분마다 실행
nohup python run.py --scheduler &

# 또는 tmux/screen 사용
tmux new -s kice
python run.py --scheduler
# Ctrl+B, D 로 분리
```

---

## 파일 목록 요약

```
Math_KICE/
├── run.py                      # 메인 실행 스크립트
├── main.py                     # 기존 서비스 코드
├── kakao_service.py            # 카카오톡 발송 서비스
├── requirements.txt            # Python 의존성
├── .env.example                # 환경변수 템플릿
│
├── src/                        # 새 모듈 (Make.com 대체)
│   ├── __init__.py
│   ├── config.py               # 설정 관리
│   ├── google_drive_service.py # Google Drive API
│   ├── pdf_converter.py        # PDF → PNG 변환
│   ├── notion_service.py       # Notion API
│   ├── supabase_service.py     # Supabase API
│   └── workflow.py             # 워크플로우 관리
│
├── downloads/                  # PDF 다운로드 (자동 생성)
├── output/                     # 이미지 출력 (자동 생성)
├── credentials/                # 인증 정보 (자동 생성)
│
├── schema_v2.sql               # DB 스키마
├── sample_data.sql             # 샘플 데이터
├── notion_template.md          # Notion DB 템플릿
│
├── BEGINNER_GUIDE.md           # 초보자 가이드
├── SETUP_GUIDE.md              # 설정 가이드
└── PIPELINE_GUIDE.md           # 이 문서
```

---

## 예상 작업량

| 단계 | 작업 | 예상 시간 |
|------|------|----------|
| 환경 준비 | Python 설치 + 계정 가입 + 설정 | 1~2시간 |
| PDF 수집 | 16개 파일 다운로드 | 30분 |
| 자동 추출 | python run.py 실행 | 30분 |
| 검수 | 480문항 × 2분 | 16시간 (2~3일) |
| 카카오 설정 | 채널 + 연동 | 1~2시간 |
| **총계** | | **약 20시간** |

---

## 트러블슈팅

### Google Drive 인증 실패
```bash
# 토큰 삭제 후 재인증
del credentials\google_token.json
python run.py
```

### PDF 변환 오류
- PDF 파일이 손상되지 않았는지 확인
- PyMuPDF 설치 확인: `pip install PyMuPDF`

### Notion 연결 오류
- Integration이 데이터베이스에 연결되었는지 확인
- 데이터베이스 ID가 정확한지 확인

### Supabase 연결 오류
- URL 형식 확인: `https://xxxxxxxx.supabase.co`
- API 키가 올바른지 확인

### KakaoTalk "네트워크 연결 상태" 에러
- **원인**: 메시지 버튼에 localhost URL 사용
- **해결**: `server/kakao_message.py`에서 localhost URL 체크
```python
# 버튼에 localhost URL이면 버튼 추가하지 않음
if button_url and "localhost" not in button_url:
    template["buttons"] = [{"title": ..., "link": ...}]
```

### 이미지가 흐릿함
- **원인**: 저해상도 PDF 변환 후 업스케일
- **해결**: 250 DPI로 변환 후 1600px로 다운스케일
```python
# 고해상도 변환 (250 DPI)
dpi = 250
zoom = dpi / 72
pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
# 결과: 2924x4136 px

# 다운스케일 (1600px) - image_processor.py
new_width = 1600
# 다운스케일 = 선명, 업스케일 = 흐릿
```

### DB 이미지 URL 404
- **원인**: DB의 `image_url`과 실제 파일명 불일치
- **해결**: 업로드 시 `{problem_id}.png` 형식 사용
```python
# DB: 2026_CSAT_Q01
# 파일: 2026_CSAT_Q01.png (O)
# 파일: page_001.png (X - 불일치)
storage.upload_image(local_path, f'{problem_id}.png')
```

---

## NEW: 하이브리드 분리 기능 (Hybrid Split)

### 개요

한 페이지에 여러 문제가 있는 KICE 수학 시험지를 자동으로 분리하는 기능입니다.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 1. 템플릿    │────►│ 2. OCR 검증 │────►│ 3. 수동 보정 │
│ 자동 분리    │     │ (문제번호   │     │ (오류 건만) │
│ (무료)      │     │  확인)      │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
     100%                95%                5%
```

### 사용 방법

```bash
# 기본 실행 (하이브리드 분리 활성화)
python src/pipeline.py --pdf "경로/시험지.pdf" --year 2024 --exam CSAT

# OCR 검증 없이 (빠른 처리)
python src/pipeline.py --pdf "경로/시험지.pdf" --year 2024 --exam CSAT --no-ocr

# 기존 방식 사용 (1페이지=1문항 가정)
python src/pipeline.py --pdf "경로/시험지.pdf" --year 2024 --exam CSAT --no-hybrid
```

### 템플릿 구조 (수능 수학)

| 페이지 | 문제 번호 | 비고 |
|--------|----------|------|
| 1 | Q1~Q2 | 객관식 |
| 2 | Q3~Q5 | 객관식 |
| 3 | Q6~Q8 | 객관식 |
| 4 | Q9~Q10 | 객관식 |
| 5 | Q11~Q12 | 객관식 |
| 6 | Q13~Q14 | 객관식 |
| 7 | Q15 | 객관식 마지막 |
| 8 | Q16~Q17 | 단답형 시작 |
| 9 | Q18~Q19 | 단답형 |
| 10 | Q20~Q21 | 단답형 |
| 11 | Q22 | 단답형 마지막 |

### OCR 검증

- pytesseract 설치 필요: `pip install pytesseract`
- Tesseract OCR 설치 필요: https://github.com/tesseract-ocr/tesseract
- 문제 번호 자동 검출하여 템플릿 결과 검증
- 불일치 시 `needs_review` 플래그 설정

### 수동 검토

분리 결과는 `{output_dir}/split_summary.json`에 저장됩니다:

```json
{
  "exam": "CSAT",
  "year": 2024,
  "total_problems": 22,
  "needs_review_count": 2,
  "needs_review": ["2024_CSAT_Q15", "2024_CSAT_Q21"],
  "results": [...]
}
```

### 관련 파일

- `src/page_splitter.py` - 하이브리드 분리 모듈
- `src/pipeline.py` - 통합 파이프라인

---

## 다음 단계 (확장)

1. ~~**문제 이미지 자동 크롭** - AI 기반 문항 영역 인식~~ ✅ 완료 (하이브리드 분리)
2. **단원 자동 분류** - GPT/Claude API 활용
3. **학습 분석 대시보드** - 사용자 통계 시각화
4. **오답 노트 자동 생성** - 틀린 문제 기반 복습
