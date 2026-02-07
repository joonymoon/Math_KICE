#!/usr/bin/env python3
"""
KICE 수학 문제 관리 시스템 - 실행 스크립트

사용법:
    # 한 번 실행 (새 파일 처리)
    python run.py

    # 스케줄러 모드 (30분마다 실행)
    python run.py --scheduler

    # 스케줄러 모드 (사용자 지정 간격)
    python run.py --scheduler --interval 60

    # 로컬 PDF 처리
    python run.py --local path/to/file.pdf

    # 통계만 출력
    python run.py --stats

    # Notion 동기화만 실행
    python run.py --sync

    # 설정 확인
    python run.py --check
"""

import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))


def main():
    parser = argparse.ArgumentParser(
        description="KICE 수학 문제 관리 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--scheduler",
        action="store_true",
        help="스케줄러 모드로 실행 (주기적 실행)"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="스케줄러 실행 간격 (분, 기본값: 30)"
    )

    parser.add_argument(
        "--local",
        type=str,
        help="로컬 PDF 파일 처리"
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="통계만 출력"
    )

    parser.add_argument(
        "--sync",
        action="store_true",
        help="Notion → Supabase 동기화만 실행"
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="설정 확인만 수행"
    )

    parser.add_argument(
        "--send-daily",
        action="store_true",
        help="일일 문제 발송 스케줄러 실행 (5분 간격 체크)"
    )

    parser.add_argument(
        "--send-once",
        action="store_true",
        help="일일 문제 발송 1회 실행 후 종료"
    )

    args = parser.parse_args()

    # 설정 확인 모드
    if args.check:
        from src.config import validate_config, print_config
        print("\n설정 확인 중...")
        print_config()
        if validate_config():
            print("\n[OK] 모든 설정이 올바릅니다.")
        else:
            print("\n[ERROR] 설정 오류가 있습니다. .env 파일을 확인하세요.")
        return

    # 로컬 PDF 처리 모드
    if args.local:
        from src.workflow import process_single_pdf
        process_single_pdf(args.local)
        return

    # 통계 출력 모드
    if args.stats:
        from src.supabase_service import SupabaseService
        service = SupabaseService()
        service.print_stats()
        return

    # Notion 동기화 모드
    if args.sync:
        from src.notion_service import NotionService
        from src.supabase_service import SupabaseService

        notion = NotionService()
        supabase = SupabaseService()

        synced = notion.sync_to_supabase(supabase)
        print(f"\n동기화 완료: {len(synced)}개")
        return

    # 일일 문제 발송
    if args.send_daily or args.send_once:
        from server.scheduler import DailyScheduler
        scheduler = DailyScheduler()
        if args.send_once:
            scheduler.run_once()
        else:
            scheduler.run_loop(check_interval_minutes=args.interval)
        return

    # 메인 워크플로우 실행
    from src.workflow import KICEWorkflow

    workflow = KICEWorkflow()

    if args.scheduler:
        # 스케줄러 모드
        workflow.run_scheduler(interval_minutes=args.interval)
    else:
        # 한 번 실행
        workflow.run_once()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n프로그램 종료")
        sys.exit(0)
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
