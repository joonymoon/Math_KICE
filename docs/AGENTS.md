# KICE Math 에이전트 시스템 가이드

## 에이전트 구조 (6개)

```
Commander (총괄)
├── PipelineAgent  (PDF 처리 파이프라인)
├── ContentAgent   (Notion 동기화/콘텐츠 검증)
├── OpsAgent       (통계/헬스체크/모니터링)
├── DevAgent       (서버 관리/의존성/코드 통계)
└── QAAgent        (import 검증/구문 검사/API 테스트)
```

## 에이전트별 역할

### Commander (`agents/commander.py`)
- **역할**: 전체 프로젝트 조율 및 의사결정
- **기능**: 작업 분배, 우선순위, 에이전트 간 충돌 해결, 상태 보고
- **키워드 디스패치**: 메시지 내 키워드로 적절한 에이전트 자동 선택

### PipelineAgent (`agents/pipeline_agent.py`)
- **역할**: PDF 처리 파이프라인
- **키워드**: pdf, pipeline, 파이프라인, drive, 변환, 업로드, 정답
- **담당 파일**: `src/pipeline.py`, `src/pdf_converter.py`, `src/page_splitter.py`

### ContentAgent (`agents/content_agent.py`)
- **역할**: Notion 동기화, 데이터 검증, 콘텐츠 QA
- **키워드**: notion, 동기화, sync, 검수, 검증, validate, 콘텐츠
- **담당 파일**: `src/notion_service.py`, `sync_to_notion.py`

### OpsAgent (`agents/ops_agent.py`)
- **역할**: 통계, 헬스체크, 모니터링, 무결성 검사
- **키워드**: 통계, stats, health, 헬스, 보고, report, 무결성
- **담당 파일**: `src/supabase_service.py` (통계 관련)

### DevAgent (`agents/dev_agent.py`)
- **역할**: 서버 관리, 의존성 체크, 코드 통계
- **키워드**: 서버, server, 의존성, dep, 구조, structure, 개발
- **액션**: check-server, start-server, stop-server, deps, structure, code-stats

### QAAgent (`agents/qa_agent.py`)
- **역할**: import 검증, 구문 검사, API 테스트, 종합 품질 검사
- **키워드**: 테스트, test, import, syntax, 구문, 품질, qa, endpoint
- **액션**: imports, syntax, config, endpoints, full-check

## CLI 사용법

```bash
# 전체 현황
python -m agents.run_agents status

# 파이프라인
python -m agents.run_agents pipeline --year 2026

# 콘텐츠
python -m agents.run_agents content validate
python -m agents.run_agents content sync

# 운영
python -m agents.run_agents ops stats
python -m agents.run_agents ops health
python -m agents.run_agents ops report --year 2026
python -m agents.run_agents ops integrity

# 개발
python -m agents.run_agents dev check-server
python -m agents.run_agents dev deps
python -m agents.run_agents dev code-stats

# QA
python -m agents.run_agents qa imports
python -m agents.run_agents qa syntax
python -m agents.run_agents qa full-check
```

## 파일 구조

```
agents/
├── __init__.py          # 패키지 초기화 (6개 에이전트 export)
├── base.py              # BaseAgent, Task, TaskStatus, TaskPriority
├── commander.py         # CommanderAgent (총괄 + 디스패치)
├── pipeline_agent.py    # PipelineAgent (PDF 처리)
├── content_agent.py     # ContentAgent (Notion/콘텐츠)
├── ops_agent.py         # OpsAgent (통계/모니터링)
├── dev_agent.py         # DevAgent (서버/의존성)
├── qa_agent.py          # QAAgent (테스트/검증)
└── run_agents.py        # CLI 인터페이스
```

---

**마지막 업데이트**: 2026-02-08
