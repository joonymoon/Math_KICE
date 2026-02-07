# KICE Math 설정 가이드

## 필수 환경 변수 (.env)

```env
# Supabase (필수)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# Google Drive (필수)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_DRIVE_FOLDER_ID=your-drive-folder-id

# Notion (필수)
NOTION_TOKEN=secret_your-integration-token
NOTION_DATABASE_ID=your-database-id

# 카카오 (선택)
KAKAO_REST_API_KEY=your-rest-api-key
KAKAO_REDIRECT_URI=http://localhost:8000/auth/kakao/callback

# 경로
DOWNLOAD_PATH=./downloads
OUTPUT_PATH=./output

# 개발
LOG_LEVEL=INFO
DEBUG=False
BASE_URL=http://localhost:8000
```

## 설치

```bash
pip install -r requirements.txt

# 서버 실행
python run.py
# 또는
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000

# Notion 동기화
python sync_to_notion.py
```

## Supabase 테이블 스키마

`schema_v2.sql`을 SQL Editor에서 실행. 주요 테이블:

### problems 테이블
- `problem_id` (PK): 2026_CSAT_Q01
- `year`, `exam`, `question_no`, `score`
- `answer`, `answer_verified`, `answer_type`
- `subject`, `unit`, `difficulty`
- `problem_image_url`, `solution`
- `intent_1`, `intent_2`
- `status`: needs_review / ready / sent
- `notion_page_id`: Notion 페이지 ID

### hints 테이블
- `problem_id`, `stage` (1~3)
- `hint_type`: concept_direction / key_transformation / decisive_line
- `hint_text`: 힌트 내용

### users, daily_schedules, deliveries
- 사용자 관리, 자동 발송 스케줄

## Notion 데이터베이스 (20개 속성)

| 속성 | 타입 |
|------|------|
| 문제 ID | 제목 |
| 연도, 문항번호, 배점, 난이도 | 숫자 |
| 시험, 상태, 과목, 단원, 정답유형 | 선택 |
| 정답, 출제의도, 풀이, 힌트1~3, 검수자 | 리치 텍스트 |
| 원본링크, 이미지폴더 | URL |
| 검수일 | 날짜 |

## 트러블슈팅

| 문제 | 해결 |
|------|------|
| "네트워크 연결 상태" 에러 | localhost URL → 버튼 자동 비활성화 |
| 이미지 흐릿 | 250 DPI 변환 → 1600px 다운스케일 |
| DB 이미지 404 | 업로드: `{problem_id}.png` 형식 |
| Notion rate limit | 자동 exponential backoff 재시도 |
| Windows cp949 | `python -u` 사용 |

---

**마지막 업데이트**: 2026-02-08
