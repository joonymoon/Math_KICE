# KICE Math 파이프라인 문서

## 전체 워크플로우

```
[1] PDF 수집          [2] 이미지 변환         [3] 검수
Google Drive    →    PyMuPDF (250 DPI)   →   Notion (20속성)
                           ↓                    ↓
[6] 발송             [5] 저장              [4] 동기화
KakaoTalk       ←    Supabase DB     ←    sync_to_notion.py
```

## 단계별 상세

### [1] PDF 수집
- **입력**: 수능/평가원 PDF 파일 (YYYY_EXAM_PROBLEM.pdf)
- **방법**: Admin 페이지 업로드 또는 Google Drive

### [2] 이미지 변환 (PyMuPDF)
- **설정**: 250 DPI (2924x4136 px)
- **모듈**: `src/pdf_converter.py`

### [3] 하이브리드 문항 분리
- **모듈**: `src/page_splitter.py`
- **방식**: Template + OCR 검증
- 수능 수학 11페이지 → Q1~Q22 자동 분리

### [4] 이미지 처리
- **모듈**: `src/image_processor.py`
- 헤더/푸터 제거, 공백 트림, 1600px 리사이즈

### [5] Storage 업로드
- **모듈**: `src/supabase_storage.py`
- 파일명: `{problem_id}.png`
- 버킷: `problem-images-v2` (공개)

### [6] DB 저장
- **모듈**: `src/supabase_service.py`
- problems 테이블 + hints 테이블

### [7] Notion 동기화
- **스크립트**: `sync_to_notion.py`
- **모듈**: `src/notion_service.py`
- 20개 속성 + 풍부한 본문 블록 (이미지, 풀이 토글, 힌트 토글, 체크리스트)
- Rate limiting (1.5초/문제), exponential backoff, circuit breaker

### [8] 카카오톡 발송
- **모듈**: `server/kakao_message.py`, `server/scheduler.py`
- Feed 템플릿 (이미지 + 문제풀기 버튼)

## 이미지 품질

| 단계 | 해상도 |
|------|--------|
| PDF 원본 | A4 (72 DPI) |
| 고해상도 변환 | 2924x4136 px (250 DPI) |
| 최종 출력 | 1600px (다운스케일 = 선명) |

## 에이전트 시스템 (6개)

```
Commander (총괄)
├── PipelineAgent  (PDF 처리)
├── ContentAgent   (Notion/콘텐츠)
├── OpsAgent       (통계/모니터링)
├── DevAgent       (서버/의존성)
└── QAAgent        (테스트/검증)
```

---

**마지막 업데이트**: 2026-02-08
