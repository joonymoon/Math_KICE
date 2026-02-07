# KICE Math 파이프라인 문서

## 전체 워크플로우

```
[1] PDF 수집          [2] 이미지 변환         [3] 검토
Google Drive    →    PyMuPDF (250 DPI)   →   Notion
                           ↓
[6] 발송             [5] 저장              [4] 업로드
KakaoTalk       ←    Supabase DB     ←    Supabase Storage
```

## 단계별 상세

### [1] PDF 수집 (Google Drive)
- **입력**: 수능/평가원 PDF 파일
- **출력**: `downloads/` 폴더에 저장
- **담당**: Business 에이전트

### [2] 이미지 변환 (PyMuPDF)
- **입력**: PDF 파일
- **설정**: 250 DPI (2924x4136 px)
- **출력**: `output/2026_CSAT_HIRES/page_XXX.png`
- **담당**: Developer 에이전트

```python
import fitz
dpi = 250
zoom = dpi / 72
pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
```

### [3] 이미지 처리 (ImageProcessor)
- **입력**: 고해상도 페이지 이미지
- **처리**:
  1. 헤더 제거 (480px)
  2. 푸터 제거 (350px)
  3. 하단 공백 자동 트림
  4. 1600px로 리사이즈
- **출력**: `output/2026_CSAT_FINAL/page_XXX.png`
- **담당**: Designer 에이전트

### [4] Storage 업로드 (Supabase)
- **입력**: 처리된 이미지
- **파일명**: `{problem_id}.png` (예: 2026_CSAT_Q01.png)
- **버킷**: `problem-images` (공개)
- **담당**: Developer 에이전트

### [5] DB 저장 (Supabase)
- **테이블**: `problems`
- **필드**:
  - `problem_id`: 2026_CSAT_Q01
  - `image_url`: https://xxx.supabase.co/storage/v1/object/public/problem-images/2026_CSAT_Q01.png
  - `status`: ready/sent/needs_review
- **담당**: Business 에이전트

### [6] KakaoTalk 발송
- **API**: 카카오 나에게 보내기
- **템플릿**: feed (이미지 포함)
- **담당**: Developer + QA 에이전트

## 이미지 품질 기준

| 단계 | 해상도 | 비고 |
|------|--------|------|
| PDF 원본 | A4 (595x842 pt) | 72 DPI 기준 |
| 고해상도 변환 | 2924x4136 px | 250 DPI |
| 최종 출력 | 1600x~1800 px | 다운스케일 |

## 중요: 문항-페이지 매핑

### 현재 상태 (1:1 매핑)
```
page_001.png → 2026_CSAT_Q01
page_002.png → 2026_CSAT_Q02
...
```

### 향후 개선 (다대다 매핑)
```json
{
  "2026_CSAT_Q01": {"page": 3, "region": [0, 0, 1000, 500]},
  "2026_CSAT_Q02": {"page": 3, "region": [0, 500, 1000, 1000]},
  "2026_CSAT_Q03": {"page": 4, "region": [0, 0, 1000, 800]}
}
```

## 에러 처리

### KakaoTalk 버튼 에러
```python
# kakao_message.py
if button_url and "localhost" not in button_url:
    template["buttons"] = [{"title": ..., "link": ...}]
# localhost URL은 버튼 추가하지 않음
```

### 이미지 URL 404
- DB의 `image_url`과 실제 파일명 일치 확인
- Supabase Storage 버킷 공개 설정 확인
