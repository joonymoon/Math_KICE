# KICE Math 설정 가이드

## 필수 환경 변수 (.env)

```env
# Kakao API
KAKAO_CLIENT_ID=your_kakao_app_key
KAKAO_REDIRECT_URI=http://localhost:8000/auth/kakao/callback

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_role_key

# Notion (선택)
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_database_id

# CloudConvert (선택)
CLOUDCONVERT_API_KEY=your_cloudconvert_key

# 경로
DOWNLOAD_PATH=./downloads
OUTPUT_PATH=./output
```

## 설치

```bash
# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
```

## 파이프라인 실행

### 1. PDF 변환 (수동)
```bash
python -c "
import fitz
from pathlib import Path

pdf_path = './downloads/2026_CSAT_PROBLEM.pdf'
output_dir = Path('./output/2026_CSAT_HIRES')
output_dir.mkdir(parents=True, exist_ok=True)

doc = fitz.open(pdf_path)
dpi = 250
zoom = dpi / 72

for page_num in range(len(doc)):
    page = doc[page_num]
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    pix.save(str(output_dir / f'page_{page_num + 1:03d}.png'))

doc.close()
"
```

### 2. 이미지 크롭
```bash
python src/image_processor.py ./output/2026_CSAT_HIRES ./output/2026_CSAT_FINAL
```

### 3. Supabase 업로드
```bash
python src/supabase_storage.py
```

## Supabase 테이블 스키마

### problems 테이블
```sql
CREATE TABLE problems (
    problem_id TEXT PRIMARY KEY,
    year INT,
    exam TEXT,
    question_no INT,
    score INT DEFAULT 3,
    image_url TEXT,
    status TEXT DEFAULT 'ready',
    answer TEXT,
    solution TEXT,
    hint_1 TEXT,
    hint_2 TEXT,
    hint_3 TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### users 테이블
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kakao_id TEXT UNIQUE,
    nickname TEXT,
    email TEXT,
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMPTZ,
    current_level INT DEFAULT 3,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 트러블슈팅

### "네트워크 연결 상태가 좋지 않습니다" 에러
- **원인**: KakaoTalk 버튼에 localhost URL 사용
- **해결**: kakao_message.py에서 localhost 체크 로직 확인
  ```python
  if button_url and "localhost" not in button_url:
      # 버튼 추가
  ```

### 이미지가 흐릿함
- **원인**: 저해상도 PDF 변환 후 업스케일
- **해결**: PDF를 250 DPI로 변환 (2924x4136 px)
  - 다운스케일 (2924 → 1600) = 선명
  - 업스케일 (800 → 1600) = 흐릿

### DB 이미지 URL 불일치
- **원인**: 파일명과 problem_id 불일치
- **해결**: 업로드 시 `{problem_id}.png` 형식 사용
  ```python
  storage.upload_image(local_path, f'{problem_id}.png')
  ```
