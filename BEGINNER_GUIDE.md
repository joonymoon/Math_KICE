# 수학 문제 자동화 시스템 - 초보자 가이드

이 가이드는 프로그래밍 경험이 없어도 따라할 수 있도록 기초부터 설명합니다.

---

## 목차
1. [전체 시스템 이해하기](#1-전체-시스템-이해하기)
2. [Google Drive 설정](#2-google-drive-설정)
3. [Notion 설정](#3-notion-설정)
4. [CloudConvert 설정](#4-cloudconvert-설정)
5. [Supabase 설정](#5-supabase-설정)
6. [Make.com 설정](#6-makecom-설정)
7. [전체 연결하기](#7-전체-연결하기)

---

## 1. 전체 시스템 이해하기

### 우리가 만들 시스템의 흐름

```
[수능 PDF] → [Google Drive] → [Make.com] → [Supabase DB]
                                   ↓
                              [Notion 검수]
                                   ↓
                              [카카오톡 발송]
```

### 각 서비스의 역할

| 서비스 | 역할 | 비용 |
|--------|------|------|
| **Google Drive** | PDF 파일 저장소 | 무료 (15GB) |
| **Notion** | 문제 검수 및 관리 화면 | 무료 |
| **CloudConvert** | PDF를 이미지로 변환 | 무료 (매일 25회) |
| **Supabase** | 데이터베이스 (문제/정답 저장) | 무료 (500MB) |
| **Make.com** | 자동화 연결 도구 | 무료 (1,000회/월) |

### 왜 이렇게 복잡한가요?

단순히 문제를 저장하고 보내는 것이 아니라:
- PDF에서 **자동으로** 문제를 추출
- 정답을 **자동으로** 매칭
- 검수 후 **자동으로** 카카오톡 발송

이런 자동화를 위해 여러 서비스를 연결하는 것입니다.

---

## 2. Google Drive 설정

### 2.1 Google Drive란?

구글에서 제공하는 클라우드 저장소입니다.
여기에 수능 PDF 파일을 올리면, Make.com이 자동으로 감지하고 처리합니다.

### 2.2 폴더 구조 만들기

**Step 1: Google Drive 접속**
1. https://drive.google.com 접속
2. Google 계정으로 로그인 (없으면 생성)

**Step 2: 폴더 만들기**
1. 왼쪽 상단 `+ 새로 만들기` 클릭
2. `폴더` 선택
3. 폴더 이름: `KICE_Math` 입력 → `만들기`

**Step 3: 하위 폴더 만들기**
`KICE_Math` 폴더 안에 들어가서 다음 폴더들을 만듭니다:

```
KICE_Math/
├── 01_Problems/       ← 문제 PDF 업로드
├── 02_Answers/        ← 정답 PDF 업로드
├── 03_Images/         ← 변환된 이미지 저장 (자동)
└── 04_Processed/      ← 처리 완료된 PDF 이동 (자동)
```

### 2.3 PDF 파일 이름 규칙

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
| 2023 수능 | 2023_CSAT_PROBLEM.pdf | 2023_CSAT_ANSWER.pdf |

### 2.4 PDF 파일 구하기

수능/모의고사 PDF는 공식 사이트에서 다운로드:
- **한국교육과정평가원**: https://www.suneung.re.kr
- **EBSi**: https://www.ebsi.co.kr

1. 해당 사이트 접속
2. 기출문제 → 수학 영역 선택
3. 문제지와 정답지 각각 다운로드
4. 파일명 변경 후 Google Drive에 업로드

---

## 3. Notion 설정

### 3.1 Notion이란?

메모, 데이터베이스, 칸반보드 등을 만들 수 있는 올인원 도구입니다.
우리는 **문제 검수용 대시보드**로 사용합니다.

### 3.2 Notion 가입하기

1. https://www.notion.so 접속
2. `무료로 Notion 사용하기` 클릭
3. Google 계정 또는 이메일로 가입
4. 개인용(Personal) 선택

### 3.3 검수용 데이터베이스 만들기

**Step 1: 새 페이지 만들기**
1. 왼쪽 사이드바에서 `+ 페이지 추가` 클릭
2. 페이지 이름: `수학 문제 관리` 입력
3. 빈 페이지에서 `/database` 입력
4. `데이터베이스 - 전체 페이지` 선택

**Step 2: 속성(Property) 추가하기**

테이블 상단의 `+` 버튼을 눌러 다음 속성들을 추가:

| 속성 이름 | 타입 | 설명 |
|-----------|------|------|
| Problem ID | 제목 (기본) | 2024_CSAT_COMMON_Q05 |
| Year | 숫자 | 2024 |
| Exam | 선택 | CSAT, KICE6, KICE9 |
| Q No | 숫자 | 5 |
| Score | 숫자 | 3 또는 4 |
| Answer | 텍스트 | 정답 |
| Subject | 선택 | Math1, Math2 |
| Unit | 선택 | 지수와로그, 삼각함수 등 |
| Status | 선택 | 검수필요, 검수완료, 발송완료 |
| Intent 1 | 텍스트 | 출제의도 1 |
| Intent 2 | 텍스트 | 출제의도 2 |
| Hint 1 | 텍스트 | 개념 방향 힌트 |
| Hint 2 | 텍스트 | 핵심 전환 힌트 |
| Hint 3 | 텍스트 | 결정적 한 줄 힌트 |
| Solution | 텍스트 | 상세 풀이 |

**Step 3: 선택 옵션 설정하기**

`Exam` 속성 클릭 → 옵션 추가:
- CSAT (파란색)
- KICE6 (초록색)
- KICE9 (노란색)

`Subject` 속성 클릭 → 옵션 추가:
- Math1 (빨간색)
- Math2 (보라색)

`Status` 속성 클릭 → 옵션 추가:
- 검수필요 (빨간색)
- 검수완료 (초록색)
- 발송완료 (회색)

`Unit` 속성 클릭 → 옵션 추가:
```
수학1:
- 지수와로그
- 지수함수와로그함수
- 삼각함수
- 삼각함수덧셈정리
- 수열
- 급수와합
- 수학적귀납법

수학2:
- 함수의극한
- 함수의연속
- 미분계수와도함수
- 도함수의활용
- 부정적분과정적분
- 정적분의활용
```

**Step 4: 보기(View) 만들기**

테이블 왼쪽 상단 `+ 보기 추가` 클릭:

1. **검수 대기 (보드)**
   - 보기 타입: 보드
   - 그룹화 기준: Status
   - 필터: Status = 검수필요

2. **연도별 (테이블)**
   - 보기 타입: 테이블
   - 정렬: Year 내림차순, Q No 오름차순

3. **단원별 (테이블)**
   - 보기 타입: 테이블
   - 그룹화 기준: Unit

### 3.4 Notion API 연결 (Make.com 연동용)

**Step 1: 통합(Integration) 만들기**
1. https://www.notion.so/my-integrations 접속
2. `+ 새 통합 만들기` 클릭
3. 이름: `Math Problem Manager`
4. 워크스페이스 선택
5. `제출` 클릭

**Step 2: API 키 복사**
- `내부 통합 토큰` 복사 (나중에 Make.com에서 사용)
- 형식: `secret_xxxxxxxxxxxxxxxxxxxx`

**Step 3: 데이터베이스에 통합 연결**
1. `수학 문제 관리` 페이지로 돌아가기
2. 오른쪽 상단 `···` 클릭
3. `연결` → `Math Problem Manager` 선택

---

## 4. CloudConvert 설정

### 4.1 CloudConvert란?

파일 형식을 변환해주는 서비스입니다.
PDF → PNG 이미지 변환에 사용합니다.

### 4.2 가입하기

1. https://cloudconvert.com 접속
2. `Sign Up` 클릭
3. 이메일 또는 Google로 가입

### 4.3 API 키 발급

1. 로그인 후 우측 상단 프로필 클릭
2. `Dashboard` → `API` → `API Keys`
3. `Create API Key` 클릭
4. 이름: `KICE Math`
5. Scopes: `tasks.read`, `tasks.write` 체크
6. `Create` → API 키 복사

### 4.4 무료 사용량

- **매일 25 크레딧** 무료 제공
- PDF → PNG 변환: 페이지당 약 0.5 크레딧
- 하루에 약 50페이지 변환 가능

### 4.5 사용 예시 (테스트)

1. CloudConvert 메인 페이지
2. PDF 파일 드래그 앤 드롭
3. 변환 형식: PNG 선택
4. `Convert` 클릭
5. 변환된 이미지 다운로드

---

## 5. Supabase 설정

### 5.1 Supabase란?

PostgreSQL 데이터베이스를 쉽게 사용할 수 있게 해주는 서비스입니다.
문제, 정답, 힌트, 사용자 정보를 저장합니다.

### 5.2 가입 및 프로젝트 생성

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

### 5.3 데이터베이스 테이블 생성

**Step 1: SQL 에디터 열기**
1. 왼쪽 메뉴에서 `SQL Editor` 클릭
2. `+ New query` 클릭

**Step 2: 스키마 실행**
1. `schema_v2.sql` 파일 내용 전체 복사
2. SQL 에디터에 붙여넣기
3. `Run` 버튼 클릭 (또는 Ctrl+Enter)
4. "Success" 메시지 확인

**Step 3: 샘플 데이터 입력**
1. 새 쿼리 탭 열기
2. `sample_data.sql` 파일 내용 전체 복사
3. 붙여넣기 후 `Run` 실행

**Step 4: 데이터 확인**
1. 왼쪽 메뉴 `Table Editor` 클릭
2. `problems` 테이블 클릭
3. 30개의 문제가 보이면 성공!

### 5.4 API 키 확인

**Make.com 연동에 필요한 정보:**

1. 왼쪽 메뉴 `Project Settings` (톱니바퀴)
2. `API` 탭 클릭
3. 다음 정보 메모:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public key**: `eyJhbGciOiJI...` (긴 문자열)

### 5.5 Storage 설정 (이미지 저장용)

**Step 1: 버킷 만들기**
1. 왼쪽 메뉴 `Storage` 클릭
2. `New bucket` 클릭
3. 이름: `problem-images`
4. Public bucket: ON (체크)
5. `Create bucket` 클릭

**Step 2: 정책 설정**
1. `problem-images` 버킷 클릭
2. `Policies` 탭 → `New Policy`
3. `For full customization` 선택
4. Policy name: `Public Read`
5. Allowed operation: `SELECT` 체크
6. `Review` → `Save policy`

---

## 6. Make.com 설정

### 6.1 Make.com이란?

서로 다른 앱/서비스를 연결해서 자동화하는 도구입니다.
예: "Google Drive에 파일이 올라오면 → 자동으로 처리해서 → Supabase에 저장"

### 6.2 가입하기

1. https://www.make.com 접속
2. `Get started free` 클릭
3. Google 계정 또는 이메일로 가입
4. 무료 플랜 선택

### 6.3 기본 용어 이해

| 용어 | 설명 | 예시 |
|------|------|------|
| **Scenario** | 자동화 작업 흐름 | "PDF 업로드 → 변환 → 저장" |
| **Module** | 하나의 작업 단위 | "Google Drive에서 파일 다운로드" |
| **Trigger** | 시작 조건 | "새 파일이 업로드되면" |
| **Action** | 실행할 작업 | "Supabase에 데이터 저장" |
| **Connection** | 서비스 연결 정보 | Google 계정 로그인 |

### 6.4 서비스 연결하기 (Connections)

**Google Drive 연결:**
1. 왼쪽 메뉴 `Connections` 클릭
2. `Add a connection` 클릭
3. `Google Drive` 검색 → 선택
4. Google 계정 로그인 → 권한 허용

**Notion 연결:**
1. `Add a connection` → `Notion` 검색
2. 3.4에서 복사한 API 키 입력
3. `Save` 클릭

**Supabase 연결:**
1. `Add a connection` → `Supabase` 검색
2. Project URL 입력 (5.4에서 확인)
3. API Key 입력 (anon public key)
4. `Save` 클릭

**CloudConvert 연결:**
1. `Add a connection` → `CloudConvert` 검색
2. 4.3에서 발급받은 API 키 입력
3. `Save` 클릭

### 6.5 첫 번째 시나리오 만들기 (테스트)

**간단한 테스트: Google Drive → Notion**

**Step 1: 새 시나리오 생성**
1. `Scenarios` → `Create a new scenario`
2. 빈 화면에서 `+` 클릭

**Step 2: 트리거 추가**
1. `Google Drive` 검색 → 선택
2. `Watch Files in a Folder` 선택
3. Connection: 위에서 만든 연결 선택
4. Folder: `KICE_Math/01_Problems` 선택
5. `OK` 클릭

**Step 3: 액션 추가**
1. Google Drive 모듈 오른쪽 `+` 클릭
2. `Notion` 검색 → 선택
3. `Create a Database Item` 선택
4. Database: `수학 문제 관리` 선택
5. 필드 매핑:
   - Problem ID: `{{1.name}}` (파일 이름)
6. `OK` 클릭

**Step 4: 테스트 실행**
1. 하단 `Run once` 클릭
2. Google Drive에 테스트 PDF 업로드
3. Notion에 새 항목이 생기면 성공!

---

## 7. 전체 연결하기

### 7.1 완성된 시나리오 구조

**시나리오 A: 문제 PDF 처리**
```
[Google Drive: 새 파일 감지]
         ↓
[CloudConvert: PDF → PNG 변환]
         ↓
[Supabase Storage: 이미지 업로드]
         ↓
[PDF.co: 텍스트 추출]
         ↓
[JavaScript: 문제별 분리]
         ↓
[Supabase: 문제 데이터 저장]
         ↓
[Notion: 검수 카드 생성]
```

**시나리오 B: 정답 PDF 처리**
```
[Google Drive: 정답 파일 감지]
         ↓
[PDF.co: 텍스트 추출]
         ↓
[JavaScript: 정답 파싱]
         ↓
[Supabase: 정답 업데이트]
```

### 7.2 상세 시나리오는 `make_scenarios.md` 참고

각 모듈의 상세 설정은 `make_scenarios.md` 파일에 있습니다.
이 기초 가이드를 완료한 후 참고하세요.

### 7.3 문제 해결

**Google Drive 연결 안됨:**
- 브라우저 팝업 차단 해제
- 시크릿 모드에서 다시 시도

**Notion 데이터베이스 안 보임:**
- 통합(Integration)이 데이터베이스에 연결되었는지 확인
- 3.4 Step 3 다시 확인

**Supabase 쿼리 실패:**
- SQL 문법 오류 확인
- 세미콜론(;) 빠졌는지 확인
- 테이블이 이미 존재하면 DROP TABLE 먼저 실행

**CloudConvert 크레딧 부족:**
- 다음 날까지 기다리기 (매일 리셋)
- 유료 플랜 고려

---

## 부록: 용어 사전

| 용어 | 설명 |
|------|------|
| **API** | 프로그램끼리 통신하는 방법. "API 키"는 통행증 같은 것 |
| **데이터베이스(DB)** | 정보를 체계적으로 저장하는 곳. 엑셀 시트의 고급 버전 |
| **클라우드** | 인터넷에 있는 컴퓨터/저장소. 내 컴퓨터가 아닌 곳 |
| **트리거** | "~하면"에 해당. 자동화가 시작되는 조건 |
| **JSON** | 데이터를 주고받는 형식. `{"이름": "값"}` 형태 |
| **SQL** | 데이터베이스와 대화하는 언어 |
| **버킷(Bucket)** | 파일을 담는 폴더 같은 것 (클라우드 저장소 용어) |

---

## 다음 단계

1. ✅ 이 가이드를 따라 모든 서비스 가입 완료
2. ✅ 각 서비스 연결(Connection) 완료
3. → `make_scenarios.md`로 실제 시나리오 구축
4. → `PIPELINE_GUIDE.md`로 전체 파이프라인 완성

**예상 소요 시간:**
- 이 가이드 완료: 2-3시간
- 전체 시스템 구축: 추가 3-4시간

질문이 있으면 각 서비스의 공식 문서를 참고하세요:
- Google Drive: https://support.google.com/drive
- Notion: https://www.notion.so/help
- Supabase: https://supabase.com/docs
- Make.com: https://www.make.com/en/help
