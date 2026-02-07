"""
KICE Math Agent Team - CLI 인터페이스

사용법:
    # 파이프라인
    python -m agents.run_agents pipeline --year 2026 --exam CSAT
    python -m agents.run_agents pipeline --answer-only --year 2026
    python -m agents.run_agents pipeline --local 2026_CSAT_PROBLEM.pdf

    # 콘텐츠
    python -m agents.run_agents content sync-to-notion --year 2026
    python -m agents.run_agents content sync-from-notion
    python -m agents.run_agents content validate --year 2026

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

    # 종합
    python -m agents.run_agents status
"""

import sys
import json
from pathlib import Path

# src 모듈 경로
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from .commander import CommanderAgent
from .pipeline_agent import PipelineAgent
from .content_agent import ContentAgent
from .ops_agent import OpsAgent
from .dev_agent import DevAgent
from .qa_agent import QAAgent


class AgentTeam:
    """에이전트 팀 - 초기화 및 CLI 실행"""

    def __init__(self):
        self.commander = CommanderAgent()
        self.pipeline = PipelineAgent()
        self.content = ContentAgent()
        self.ops = OpsAgent()
        self.dev = DevAgent()
        self.qa = QAAgent()

        # Commander에 에이전트 등록
        self.commander.register_agent(self.pipeline)
        self.commander.register_agent(self.content)
        self.commander.register_agent(self.ops)
        self.commander.register_agent(self.dev)
        self.commander.register_agent(self.qa)

    def print_result(self, result):
        """결과를 보기 좋게 출력"""
        if isinstance(result, str):
            print(result)
        elif isinstance(result, dict):
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        else:
            print(result)


def cmd_pipeline(team: AgentTeam, args):
    """파이프라인 명령 처리"""
    if args.answer_only:
        result = team.pipeline.process_answers(
            year=args.year,
            exam=args.exam,
        )
    elif args.local:
        result = team.pipeline.upload_local_pdf(
            pdf_path=args.local,
            year=args.year or 2026,
            exam=args.exam or "CSAT",
        )
    elif args.status:
        result = team.pipeline.get_pipeline_status()
    else:
        result = team.pipeline.run_full_pipeline(
            year=args.year,
            exam=args.exam,
            dry_run=args.dry_run,
            no_move=args.no_move,
        )
    team.print_result(result)


def cmd_content(team: AgentTeam, args):
    """콘텐츠 명령 처리"""
    action = args.action

    if action == "sync-to-notion":
        result = team.content.sync_to_notion(
            year=args.year,
            exam=args.exam,
            status=args.filter_status,
            problem_id=args.problem_id,
            dry_run=args.dry_run,
        )
    elif action == "sync-from-notion":
        result = team.content.sync_from_notion()
    elif action == "validate":
        result = team.content.validate_problems(
            year=args.year,
            exam=args.exam,
        )
    elif action == "fill-content":
        result = team.content.fill_missing_content(
            year=args.year,
            exam=args.exam,
            dry_run=args.dry_run,
        )
    elif action == "review-status":
        result = team.content.get_review_status()
    else:
        print(f"알 수 없는 액션: {action}")
        return

    team.print_result(result)


def cmd_ops(team: AgentTeam, args):
    """운영 명령 처리"""
    action = args.action

    if action == "stats":
        result = team.ops.get_stats()
    elif action == "health":
        result = team.ops.health_check()
    elif action == "report":
        report_text = team.ops.print_report(year=args.year)
        print(report_text)
        return
    elif action == "integrity":
        result = team.ops.check_data_integrity()
    else:
        print(f"알 수 없는 액션: {action}")
        return

    team.print_result(result)


def cmd_dev(team: AgentTeam, args):
    """개발 명령 처리"""
    action = args.action

    if action == "check-server":
        result = team.dev.check_server()
    elif action == "start-server":
        result = team.dev.start_server()
    elif action == "stop-server":
        result = team.dev.stop_server()
    elif action == "deps":
        result = team.dev.check_dependencies()
    elif action == "structure":
        result = team.dev.get_project_structure()
    elif action == "code-stats":
        result = team.dev.get_code_stats()
    else:
        print(f"알 수 없는 액션: {action}")
        return

    team.print_result(result)


def cmd_qa(team: AgentTeam, args):
    """QA 명령 처리"""
    action = args.action

    if action == "imports":
        result = team.qa.check_imports()
    elif action == "syntax":
        result = team.qa.check_syntax()
    elif action == "config":
        result = team.qa.validate_config()
    elif action == "endpoints":
        result = team.qa.test_endpoints()
    elif action == "full-check":
        result = team.qa.run_full_check()
    else:
        print(f"알 수 없는 액션: {action}")
        return

    team.print_result(result)


def cmd_status(team: AgentTeam, args):
    """전체 상태 보고"""
    print(team.commander.generate_status_report())


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="KICE Math Agent Team",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python -m agents.run_agents ops stats              # DB 통계
  python -m agents.run_agents ops health             # 서비스 헬스체크
  python -m agents.run_agents content validate       # 데이터 검증
  python -m agents.run_agents pipeline --year 2026   # 파이프라인 실행
  python -m agents.run_agents dev code-stats         # 코드 통계
  python -m agents.run_agents qa full-check          # 종합 품질 검사
  python -m agents.run_agents status                 # 전체 현황
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="실행할 명령")

    # ─── pipeline ───
    p_pipe = subparsers.add_parser("pipeline", help="PDF 처리 파이프라인")
    p_pipe.add_argument("--year", type=int, help="연도 필터")
    p_pipe.add_argument("--exam", choices=["CSAT", "KICE6", "KICE9"], help="시험 유형")
    p_pipe.add_argument("--answer-only", action="store_true", help="정답만 처리")
    p_pipe.add_argument("--local", help="로컬 PDF 경로")
    p_pipe.add_argument("--dry-run", action="store_true", help="미리보기")
    p_pipe.add_argument("--no-move", action="store_true", help="파일 이동 안함")
    p_pipe.add_argument("--status", action="store_true", help="파이프라인 현황")
    p_pipe.set_defaults(func=cmd_pipeline)

    # ─── content ───
    p_content = subparsers.add_parser("content", help="콘텐츠 관리 (Notion 동기화/검증)")
    p_content.add_argument(
        "action",
        choices=["sync-to-notion", "sync-from-notion", "validate", "fill-content", "review-status"],
        help="실행할 액션",
    )
    p_content.add_argument("--year", type=int, help="연도 필터")
    p_content.add_argument("--exam", choices=["CSAT", "KICE6", "KICE9"], help="시험 유형")
    p_content.add_argument("--problem-id", help="단일 문제 ID")
    p_content.add_argument("--filter-status", help="상태 필터 (ready, needs_review 등)")
    p_content.add_argument("--dry-run", action="store_true", help="미리보기")
    p_content.set_defaults(func=cmd_content)

    # ─── ops ───
    p_ops = subparsers.add_parser("ops", help="운영 관리 (통계/헬스체크)")
    p_ops.add_argument(
        "action",
        choices=["stats", "health", "report", "integrity"],
        help="실행할 액션",
    )
    p_ops.add_argument("--year", type=int, help="연도 필터 (report용)")
    p_ops.set_defaults(func=cmd_ops)

    # ─── dev ───
    p_dev = subparsers.add_parser("dev", help="개발 관리 (서버/의존성/코드)")
    p_dev.add_argument(
        "action",
        choices=["check-server", "start-server", "stop-server", "deps", "structure", "code-stats"],
        help="실행할 액션",
    )
    p_dev.set_defaults(func=cmd_dev)

    # ─── qa ───
    p_qa = subparsers.add_parser("qa", help="품질 보증 (테스트/검증)")
    p_qa.add_argument(
        "action",
        choices=["imports", "syntax", "config", "endpoints", "full-check"],
        help="실행할 액션",
    )
    p_qa.set_defaults(func=cmd_qa)

    # ─── status ───
    p_status = subparsers.add_parser("status", help="전체 시스템 현황")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 에이전트 팀 초기화
    print("=" * 55)
    print("  KICE Math Agent Team")
    print("=" * 55)

    team = AgentTeam()

    print()

    # 명령 실행
    args.func(team, args)


if __name__ == "__main__":
    main()
