# 서비스 가입 및 설정 가이드

## 필수 가입 목록

| 서비스 | 필수 | 용도 | 예상 시간 | 비용 |
|--------|------|------|----------|------|
| Python | O | 자동화 스크립트 실행 | 10분 | 무료 |
| Supabase | O | DB, Storage | 10분 | 무료 |
| Google Cloud | O | Drive API 인증 | 15분 | 무료 |
| Google Drive | O | PDF 저장소 | 5분 | 무료 |
| Notion | O | 검수 대시보드 | 10분 | 무료 |
| 카카오 개발자 | 선택 | 카카오 로그인/메시지 | 10분 | 무료 |
| 카카오톡 채널 | 선택 | 채널 메시지 발송 | 10분 | 무료 |

---

## 1. Python 설치

### 1.1 다운로드 및 설치

**Windows:**
1. https://www.python.org/downloads/ 접속
2. `Download Python 3.11.x` 버튼 클릭
3. 다운로드된 파일 실행
4. ⚠️ **중요!** `Add Python to PATH` 체크
5. `Install Now` 클릭

**Mac:**
```bash
# Homebrew 사용
brew install python@3.11
```

### 1.2 설치 확인
```bash
python --version
# Python 3.11.x 표시되면 성공
```

### 1.3 프로젝트 의존성 설치
```bash
cd Math_KICE
pip install -r requirements.txt
```

---

## 2. Supabase 가입 및 설정

### 2.1 가입
1. https://supabase.com 접속
2. "Start your project" 클릭
3. GitHub 계정으로 로그인

### 2.2 프로젝트 생성
1. "New Project" 클릭
2. 프로젝트 이름: `kice-math` (원하는 이름)
3. Database Password: 안전한 비밀번호 설정 (저장해두기!)
4. Region: `Northeast Asia (Seoul)` 선택
5. "Create new project" 클릭 (2~3분 소요)

### 2.3 DB 스키마 생성
1. 좌측 메뉴 "SQL Editor" 클릭
2. "New query" 클릭
3. `schema_v2.sql` 파일 내용 전체 복사 붙여넣기
4. "Run" 클릭
5. (선택) `sample_data.sql` 파일도 동일하게 실행

### 2.4 API 키 확인
1. 좌측 메뉴 "Project Settings" > "API"
2. 다음 값들을 `.env` 파일에 복사:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` → `SUPABASE_KEY`

---

## 3. Google Cloud 설정

### 3.1 프로젝트 생성
1. https://console.cloud.google.com 접속
2. Google 계정으로 로그인
3. 상단 프로젝트 드롭다운 → `새 프로젝트`
4. 프로젝트 이름: `KICE-Math` → `만들기`

### 3.2 Google Drive API 활성화
1. 왼쪽 메뉴 `API 및 서비스` → `라이브러리`
2. `Google Drive API` 검색 → 선택 → `사용`

### 3.3 OAuth 동의 화면 설정
1. `API 및 서비스` → `OAuth 동의 화면`
2. User Type: `External` 선택 → `만들기`
3. 앱 이름: `KICE Math` 입력
4. 사용자 지원 이메일, 개발자 연락처 입력
5. `저장 후 계속`
6. 범위 추가:
   - `https://www.googleapis.com/auth/drive.readonly`
   - `https://www.googleapis.com/auth/drive.file`
7. 테스트 사용자에 본인 이메일 추가 (선택)
8. `저장 후 계속` → 완료

### 3.4 OAuth 클라이언트 ID 생성
1. `API 및 서비스` → `사용자 인증 정보`
2. `+ 사용자 인증 정보 만들기` → `OAuth 클라이언트 ID`
3. 애플리케이션 유형: `데스크톱 앱`
4. 이름: `KICE Math Client`
5. `만들기` 클릭
6. **클라이언트 ID**와 **클라이언트 보안 비밀번호** 복사
7. `.env` 파일에 저장:
   ```
   GOOGLE_CLIENT_ID=xxxxxxxx.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxx
   ```

---

## 4. Google Drive 설정

### 4.1 폴더 생성
1. https://drive.google.com 접속
2. `+ 새로 만들기` → `폴더` → `KICE_Math`

### 4.2 폴더 ID 확인
1. 폴더 열기
2. URL에서 폴더 ID 복사:
   ```
   https://drive.google.com/drive/folders/XXXXXXXXXXXXXXXXX
                                         ↑ 폴더 ID
   ```
3. `.env` 파일에 저장:
   ```
   GOOGLE_DRIVE_FOLDER_ID=XXXXXXXXXXXXXXXXX
   ```

---

## 5. Notion 설정

### 5.1 가입
1. https://www.notion.so 접속
2. Google 계정 또는 이메일로 가입

### 5.2 데이터베이스 생성
1. `+ 페이지 추가` → `수학 문제 관리`
2. `/database` 입력 → `데이터베이스 - 전체 페이지` 선택
3. 속성 추가 (BEGINNER_GUIDE.md 참고)

### 5.3 Internal Integration 생성
1. https://www.notion.so/my-integrations 접속
2. `+ 새 통합 만들기`
3. 이름: `KICE Math`
4. 유형: `Internal`
5. `제출`
6. **내부 통합 토큰** 복사 → `.env` 파일:
   ```
   NOTION_TOKEN=secret_xxxxxxxxxxxx
   ```

### 5.4 데이터베이스에 Integration 연결 (중요!)
1. `수학 문제 관리` 페이지 열기
2. 오른쪽 상단 `···` 클릭
3. `연결` → `KICE Math` 선택

### 5.5 데이터베이스 ID 확인
1. 데이터베이스 URL에서 ID 복사:
   ```
   https://www.notion.so/XXXXXXXXXXXXXXXX?v=...
                        ↑ 데이터베이스 ID
   ```
2. `.env` 파일에 저장:
   ```
   NOTION_DATABASE_ID=XXXXXXXXXXXXXXXX
   ```

---

## 6. 카카오 설정 (선택)

### 6.1 개발자 등록
1. https://developers.kakao.com 접속
2. 카카오 계정으로 로그인
3. 개발자 등록 동의

### 6.2 애플리케이션 생성
1. "내 애플리케이션" > "애플리케이션 추가하기"
2. 앱 이름: `수학문제배달`
3. "저장" 클릭

### 6.3 플랫폼 등록
1. 생성된 앱 클릭 > "플랫폼"
2. "Web" > "사이트 도메인" 추가:
   - `http://localhost:8000`

### 6.4 카카오 로그인 설정
1. "카카오 로그인" 메뉴 > "활성화 설정" ON
2. "Redirect URI" 등록:
   - `http://localhost:8000/auth/kakao/callback`
3. "동의항목" > `talk_message` 필수로 설정

### 6.5 앱 키 확인
1. "앱 키" 메뉴
2. `REST API 키` 복사 → `.env` 파일:
   ```
   KAKAO_REST_API_KEY=xxxxxxxxxxxxxxxx
   ```

---

## 7. 카카오톡 채널 설정 (선택)

### 7.1 채널 생성
1. https://center-pf.kakao.com 접속
2. "새 채널 만들기" 클릭
3. 채널 이름: `오늘의 수학문제`
4. "채널 개설" 클릭

### 7.2 카카오 개발자와 연결
1. 카카오 개발자 > 앱 선택 > "카카오톡 채널"
2. "채널 연결" 클릭
3. 방금 만든 채널 선택

---

## 최종 .env 파일 예시

```env
# ============================================
# Supabase 설정 (필수)
# ============================================
SUPABASE_URL=https://xxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# ============================================
# Google Drive 설정 (필수)
# ============================================
GOOGLE_CLIENT_ID=xxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxx
GOOGLE_DRIVE_FOLDER_ID=1xEaZ3p2odrzPHWy54URkh0lA-dn_oEA8

# ============================================
# Notion 설정 (필수)
# ============================================
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxx

# ============================================
# 로컬 경로 (선택)
# ============================================
DOWNLOAD_PATH=./downloads
OUTPUT_PATH=./output

# ============================================
# 카카오 설정 (선택)
# ============================================
KAKAO_REST_API_KEY=xxxxxxxxxxxxxxxx
KAKAO_REDIRECT_URI=http://localhost:8000/auth/kakao/callback

# ============================================
# 개발 설정
# ============================================
LOG_LEVEL=INFO
DEBUG=False
```

---

## 설정 확인

모든 설정이 완료되면 다음 명령어로 확인:

```bash
python run.py --check
```

성공 시 출력:
```
==================================================
KICE 수학 문제 관리 시스템 설정
==================================================
Supabase URL: https://xxxxxxxx.supabas...
Google Drive 폴더: 1xEaZ3p2odrzPHWy54URkh0lA-dn_oEA8
Notion Database: xxxxxxxxxxxxxxxxxxxxxxxx
다운로드 경로: c:\Math_KICE\downloads
출력 경로: c:\Math_KICE\output
디버그 모드: False
==================================================

✓ 모든 설정이 올바릅니다.
```

---

## 체크리스트

- [ ] Python 3.11+ 설치 완료
- [ ] `pip install -r requirements.txt` 완료
- [ ] Supabase 프로젝트 생성
- [ ] `schema_v2.sql` 실행
- [ ] Google Cloud 프로젝트 생성
- [ ] Google Drive API 활성화
- [ ] OAuth 클라이언트 ID 생성
- [ ] Google Drive 폴더 생성 및 ID 확인
- [ ] Notion Internal Integration 생성
- [ ] Notion 데이터베이스에 Integration 연결
- [ ] `.env` 파일 설정 완료
- [ ] `python run.py --check` 성공
- [ ] (선택) 카카오 개발자 등록
- [ ] (선택) 카카오톡 채널 개설

---

## 다음 단계

1. `python run.py` 실행 (첫 실행 시 Google 인증 필요)
2. Google Drive에 PDF 업로드
3. 다시 `python run.py` 실행
4. Notion에서 검수 시작
