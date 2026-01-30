# KICE 수학 문제 자동화 파이프라인 가이드

## 전체 시스템 개요

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              전체 파이프라인 흐름                                    │
└─────────────────────────────────────────────────────────────────────────────────────┘

  [1] PDF 수집          [2] 자동 추출           [3] 검수            [4] 발송
  ─────────────        ─────────────          ─────────────       ─────────────

  KICE 공식 사이트      Make.com               Notion              카카오톡
       │               시나리오 A/B            검수 대시보드         채널 메시지
       │                    │                     │                    │
       ▼                    ▼                     ▼                    ▼
  ┌─────────┐         ┌─────────┐           ┌─────────┐          ┌─────────┐
  │ Google  │────────►│ PDF     │──────────►│ 사람    │─────────►│ 사용자  │
  │ Drive   │         │ 파싱    │           │ 검수    │          │ 앱/웹   │
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
| 3 | Make.com | https://make.com | 자동화 |
| 4 | Notion | https://notion.so | 검수 대시보드 |
| 5 | CloudConvert | https://cloudconvert.com | PDF→이미지 |
| 6 | PDF.co | https://pdf.co | PDF→텍스트 |
| 7 | 카카오 개발자 | https://developers.kakao.com | 메시지 발송 |

### 1.2 Supabase 설정

1. 프로젝트 생성 (Region: Seoul)
2. SQL Editor에서 `schema_v2.sql` 실행
3. API 키 복사 → `.env` 파일

```bash
# .env 파일 생성
cp .env.example .env
# SUPABASE_URL, SUPABASE_KEY 입력
```

### 1.3 Google Drive 폴더 구조 생성

```
/KICE/
├── 2022/
│   ├── CSAT/
│   ├── KICE6/
│   └── KICE9/
├── 2023/
│   ├── CSAT/
│   ├── KICE6/
│   └── KICE9/
├── 2024/
│   └── ...
├── 2025/
│   └── ...
└── _pages/          ← 자동 생성됨 (PDF→이미지)
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

해당 연도/시험 폴더에 업로드:
```
/KICE/2024/CSAT/2024_CSAT_PROBLEM.pdf
/KICE/2024/CSAT/2024_CSAT_ANSWER.pdf
```

---

## Step 3: Make.com 시나리오 설정

### 3.1 시나리오 A: 문제 PDF 처리

#### 모듈 구성 순서:

```
[1] Google Drive     [2] Set Variables    [3] CloudConvert
    Watch Files  ───►    파일명 파싱   ───►    PDF→PNG
        │                                         │
        │                                         ▼
[6] Notion          [5] Supabase         [4] PDF.co
    Create Card  ◄───    Upsert      ◄───    텍스트 추출
                            ▲                    │
                            │                    ▼
                     [5-1] Iterator      [4-1] JavaScript
                                              문항 분리
```

#### 상세 설정:

**[1] Google Drive - Watch Files**
- Folder: `/KICE/` (하위 폴더 포함)
- Filter: `{{contains(fileName; "_PROBLEM")}}`

**[2] Set Variables**
```
year = {{substring(1.fileName; 0; 4)}}
exam = {{get(split(1.fileName; "_"); 1)}}
drive_link = {{1.webViewLink}}
```

**[3] CloudConvert - Create Job**
- PDF → PNG (200 dpi)
- Output folder: `/KICE/_pages/{{year}}/{{exam}}/`

**[4] PDF.co - PDF to Text**
- Input: Google Drive File ID

**[4-1] JavaScript - 문항 분리**
- `make_js_modules.js`의 "모듈 1" 코드 복사

**[5] Iterator**
- Source: `{{4-1.items}}`

**[5-1] Supabase - Insert Row**
- Table: `problems`
- ON CONFLICT: `problem_id`

**[6] Notion - Create Database Item**
- Database: `KICE Problem Review`

---

### 3.2 시나리오 B: 정답 PDF 처리

#### 모듈 구성:

```
[1] Google Drive     [2] Set Variables    [3] PDF.co
    Watch Files  ───►    파일명 파싱   ───►    텍스트 추출
                                                  │
                                                  ▼
                     [5] Supabase         [4] JavaScript
                         Update      ◄───     정답표 파싱
                            ▲                    │
                            │                    ▼
                     [4-1] Iterator
```

**[1] Google Drive - Watch Files**
- Filter: `{{contains(fileName; "_ANSWER")}}`

**[3] PDF.co - PDF to Text**
**[4] JavaScript - 정답표 파싱**
- `make_js_modules.js`의 "모듈 2" 코드 복사

**[5] Supabase - Update Row**
- Filter: `year = {{item.year}} AND exam = {{item.exam}} AND question_no = {{item.question_no}}`
- Update: `answer = {{item.answer}}`

---

### 3.3 시나리오 C: 검수 완료 동기화 (선택)

```
[1] Notion Watch    [2] Supabase Update    [3] Supabase Insert
    (Status=Ready) ───►    problems     ───►    hints
```

---

## Step 4: Notion 검수 대시보드 설정

### 4.1 Database 생성

1. 새 페이지 → Database - Full page
2. 이름: `KICE Problem Review`
3. `notion_template.md` 참고하여 Properties 추가

### 4.2 Make.com Integration 연결

1. Notion Settings → Connections
2. Make 검색 → 연결
3. Database에 권한 부여

### 4.3 Views 생성

1. **Needs Review** (Board) - 기본 작업 뷰
2. **Ready Export** (Table) - 완료 항목
3. **By Year** (Table) - 연도별 확인

---

## Step 5: 검수 작업 (수동)

### 5.1 검수 프로세스

```
┌─────────────────────────────────────────────────────────────────┐
│  Notion "Needs Review" 보드에서 카드 클릭                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. 자동 추출 확인                                               │
│     - Score(auto), Answer(auto) 확인                            │
│     - Extract Text로 문제 내용 파악                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. 분류 확정                                                    │
│     - Subject(verify): Math1 / Math2                            │
│     - Unit(verify): 단원 선택                                    │
│     - Score(verify): 배점 확정                                   │
│     - Answer(verify): 정답 확정                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. 이미지 확인                                                  │
│     - Page Images Folder 링크 클릭                               │
│     - 해당 문항 페이지 찾기                                       │
│     - Img Page Refs에 페이지 번호 입력 (예: p03-p04)              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. 출제의도 & 힌트 작성                                         │
│     - Intent 1: 첫 번째 줄                                       │
│     - Intent 2: 두 번째 줄                                       │
│     - Hint 1: 개념 방향                                          │
│     - Hint 2: 핵심 전환                                          │
│     - Hint 3: 결정적 한 줄                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. 완료                                                         │
│     - Status → "Ready"                                          │
│     - (자동) Supabase 동기화                                     │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 힌트 작성 가이드

| 단계 | 이름 | 역할 | 예시 |
|------|------|------|------|
| Hint 1 | 개념 방향 | 어떤 개념/공식 사용? | "로그의 기본 성질을 활용하는 문제입니다." |
| Hint 2 | 핵심 전환 | 어떻게 변환/해석? | "log a = x로 치환하면 일차방정식이 됩니다." |
| Hint 3 | 결정적 한 줄 | 정답으로 가는 열쇠 | "x를 구한 후 10^x를 계산하세요." |

---

## Step 6: 카카오톡 발송 설정

### 6.1 카카오 개발자 설정

1. https://developers.kakao.com 로그인
2. 애플리케이션 생성
3. 플랫폼 등록 (Web)
4. 카카오 로그인 활성화
5. 동의항목: `talk_message` 필수

### 6.2 카카오톡 채널 개설

1. https://center-pf.kakao.com
2. 채널 생성
3. 카카오 개발자 앱과 연결

### 6.3 발송 테스트

```python
# main.py 실행
python main.py
```

---

## Step 7: 일일 자동 발송 설정

### 7.1 Supabase Cron 설정

```sql
-- 매일 00:00에 스케줄 생성
SELECT cron.schedule(
  'create-daily-schedules',
  '0 0 * * *',
  $$SELECT create_daily_schedules()$$
);
```

### 7.2 Make.com 발송 시나리오

```
[1] Schedule         [2] Supabase          [3] HTTP
    (매 분)      ───►    Query         ───►    카카오 API
                     (발송 대기 조회)
```

---

## 파일 목록 요약

```
Math_KICE/
├── schema_v2.sql           # DB 스키마 (Make 최적화)
├── sample_data.sql         # 30문항 예시 데이터
├── main.py                 # Python 서비스 코드
├── kakao_service.py        # 카카오톡 발송 서비스
├── requirements.txt        # Python 의존성
├── .env.example            # 환경변수 템플릿
│
├── make_scenarios.md       # Make.com 시나리오 설계
├── make_js_modules.js      # Make JavaScript 코드 (복붙용)
├── notion_template.md      # Notion DB 템플릿
│
├── SETUP_GUIDE.md          # 가입 가이드
├── ARCHITECTURE.md         # 시스템 아키텍처
└── PIPELINE_GUIDE.md       # 이 문서
```

---

## 예상 작업량

| 단계 | 작업 | 예상 시간 |
|------|------|----------|
| 환경 준비 | 계정 가입 + 설정 | 2~3시간 |
| PDF 수집 | 16개 파일 다운로드 | 30분 |
| Make 시나리오 | 2개 시나리오 구축 | 2~3시간 |
| 자동 추출 | Make 실행 (자동) | 1시간 |
| 검수 | 480문항 × 2분 | 16시간 (2~3일) |
| 카카오 설정 | 채널 + 연동 | 1~2시간 |
| **총계** | | **약 25시간** |

---

## 트러블슈팅

### PDF 텍스트 추출 실패
- 스캔본인 경우 OCR 필요
- PDF.co 대신 Google Cloud Vision OCR 사용

### 문항 분리 오류
- 정규식 패턴 조정 필요
- `make_js_modules.js` 수정

### 정답표 파싱 오류
- 정답표 형식이 다를 수 있음
- 수동으로 정답 입력 (Notion에서)

### 카카오 메시지 발송 실패
- 액세스 토큰 만료 → 리프레시
- 메시지 권한 동의 확인

---

## 다음 단계 (확장)

1. **문제 이미지 자동 크롭** - AI 기반 문항 영역 인식
2. **단원 자동 분류** - GPT/Claude API 활용
3. **학습 분석 대시보드** - 사용자 통계 시각화
4. **오답 노트 자동 생성** - 틀린 문제 기반 복습
