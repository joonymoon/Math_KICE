# KICE Math 서브에이전트 가이드

## 에이전트 구조

```
Commander (총괄)
├── Developer (개발)
├── Designer (디자인/UX)
├── Business (비즈니스/데이터)
└── QA_Optimizer (품질/최적화)
```

## 에이전트별 역할

### Commander (총괄 에이전트)
- **역할**: 전체 프로젝트 조율 및 의사결정
- **책임**:
  - 작업 분배 및 우선순위 결정
  - 에이전트 간 충돌 해결
  - 최종 품질 검증
  - 사용자 커뮤니케이션

### Developer (개발 에이전트)
- **역할**: 코드 구현 및 기술적 문제 해결
- **담당 파일**:
  - `server/*.py` - FastAPI 서버
  - `src/*.py` - 핵심 서비스
  - `run.py` - 메인 실행 파일
- **핵심 작업**:
  - PDF → 이미지 변환 (250 DPI)
  - Supabase 연동
  - KakaoTalk API 통합

### Designer (디자인 에이전트)
- **역할**: 사용자 경험 및 이미지 품질 최적화
- **담당 파일**:
  - `src/image_processor.py` - 이미지 처리
  - HTML 템플릿 (대시보드 UI)
- **핵심 작업**:
  - 이미지 해상도 최적화 (1600px)
  - 헤더/푸터 자동 크롭
  - KakaoTalk 표시 최적화

### Business (비즈니스 에이전트)
- **역할**: 데이터 관리 및 비즈니스 로직
- **담당 파일**:
  - `src/notion_service.py` - Notion 연동
  - `src/supabase_service.py` - DB 서비스
  - `config/` - 설정 파일
- **핵심 작업**:
  - 문항 데이터 관리
  - 문항-페이지 매핑
  - 통계 및 리포트

### QA_Optimizer (품질/최적화 에이전트)
- **역할**: 코드 품질 검증 및 버그 탐지
- **책임**:
  - localhost URL 검출 및 수정
  - API 에러 핸들링 검증
  - 성능 최적화 제안
- **체크리스트**:
  - [ ] localhost URL 없음
  - [ ] 이미지 URL 접근 가능
  - [ ] 버튼/링크 정상 동작

## 협업 규칙

### 1. 작업 요청 형식
```
[에이전트명]야 [작업내용] 해줘
예: Developer야 PDF 변환 코드 수정해줘
```

### 2. 보고 형식
```
## [에이전트명] 보고

### 완료 항목
- [x] 항목1
- [x] 항목2

### 미완료 항목
- [ ] 항목3 (원인: ~)

### 다음 단계
- 권장 작업...
```

### 3. 파일 수정 시
- 수정 전 해당 에이전트에게 확인
- 여러 에이전트 담당 파일은 Commander 조율
- 수정 후 QA_Optimizer 검증 필수

## 현재 시스템 상태

### 해결된 이슈
- [x] localhost URL 버튼 에러
- [x] 이미지 해상도 개선 (800px → 2924px → 1600px)
- [x] DB-파일명 불일치

### 미해결 이슈
- [ ] 한 페이지 다중 문항 분리
  - 현재: 페이지 = 문항 (1:1)
  - 목표: 문항별 영역 분리
  - 담당: Developer + Designer 협업

## 파일 구조
```
Math_KICE/
├── server/           # FastAPI 서버 (Developer)
├── src/              # 핵심 서비스 (Developer + Designer)
├── config/           # 설정 파일 (Business)
├── downloads/        # PDF 원본
├── output/           # 처리된 이미지
│   └── 2026_CSAT_FINAL/  # 최종 이미지 (1600px)
└── docs/             # 문서
```
