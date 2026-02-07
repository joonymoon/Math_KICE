# 서비스 가입 및 설정 가이드

## 필수 가입 목록

| 서비스 | 필수 | 용도 | 비용 |
|--------|------|------|------|
| Python 3.11+ | O | 자동화 스크립트 | 무료 |
| Supabase | O | DB + Storage | 무료 |
| Google Cloud | O | Drive API 인증 | 무료 |
| Google Drive | O | PDF 저장소 | 무료 |
| Notion | O | 검수 대시보드 (20개 속성) | 무료 |
| 카카오 개발자 | 선택 | 카카오 로그인/메시지 | 무료 |

---

## 1. Python 설치

```bash
# Windows: https://python.org/downloads/ → "Add Python to PATH" 체크!
# Mac: brew install python@3.11

python --version  # 3.11+ 확인

cd Math_KICE
pip install -r requirements.txt
```

---

## 2. Supabase 설정

1. https://supabase.com → GitHub 로그인
2. New Project: `kice-math`, Region: `Seoul`
3. SQL Editor에서 `schema_v2.sql` 실행
4. Project Settings → API:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
```

---

## 3. Google Cloud 설정

1. https://console.cloud.google.com → 프로젝트: `KICE-Math`
2. Google Drive API 활성화
3. OAuth 동의 화면 → External → 범위: `drive.readonly`, `drive.file`
4. 사용자 인증 정보 → OAuth 클라이언트 ID → 데스크톱 앱

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_DRIVE_FOLDER_ID=your-drive-folder-id
```

---

## 4. Notion 설정

1. https://www.notion.so/my-integrations → `KICE Math` Integration 생성
2. 데이터베이스에 Integration 연결 (필수!)

```env
NOTION_TOKEN=secret_your-integration-token
NOTION_DATABASE_ID=your-database-id
```

### 데이터베이스 속성 (20개)

| 속성명 | 타입 |
|--------|------|
| 문제 ID | 제목 |
| 연도, 문항번호, 배점, 난이도 | 숫자 |
| 시험, 상태, 과목, 단원, 정답유형 | 선택 |
| 정답, 출제의도, 풀이, 힌트1~3, 검수자 | 리치 텍스트 |
| 원본링크, 이미지폴더 | URL |
| 검수일 | 날짜 |

**상태 옵션**: 검수 필요 / 수정 필요 / 보류 / 검수 완료 / 발송 준비

---

## 5. 카카오 설정 (선택)

1. https://developers.kakao.com → 앱 생성
2. 플랫폼: `http://localhost:8000`
3. 카카오 로그인 활성화, Redirect URI 등록
4. 동의항목: `talk_message` 필수

```env
KAKAO_REST_API_KEY=your-rest-api-key
KAKAO_REDIRECT_URI=http://localhost:8000/auth/kakao/callback
```

---

## 6. 개발 설정

```env
LOG_LEVEL=INFO
DEBUG=False
BASE_URL=http://localhost:8000
DOWNLOAD_PATH=./downloads
OUTPUT_PATH=./output
```

---

## 설정 확인

```bash
python run.py --check
```

## 체크리스트

- [ ] Python 3.11+ 설치
- [ ] `pip install -r requirements.txt`
- [ ] Supabase 프로젝트 + `schema_v2.sql` 실행
- [ ] Google Cloud OAuth 설정
- [ ] Notion Integration + 데이터베이스 연결
- [ ] `.env` 파일 완성
- [ ] `python run.py --check` 성공
- [ ] (선택) 카카오 개발자 등록

---

**마지막 업데이트**: 2026-02-08
