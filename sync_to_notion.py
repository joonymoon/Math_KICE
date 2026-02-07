"""
Supabase → Notion 검수 페이지 동기화

Usage:
    python sync_to_notion.py                              # 전체 문제 동기화
    python sync_to_notion.py --year 2026                  # 특정 연도만
    python sync_to_notion.py --problem-id 2026_CSAT_Q01   # 단일 문제
    python sync_to_notion.py --status needs_review        # 특정 상태만
    python sync_to_notion.py --dry-run                    # 미리보기
    python sync_to_notion.py --yes                        # 확인 없이 실행
"""

import argparse
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from src.supabase_service import SupabaseService
from src.notion_service import NotionService


def format_eta(seconds: float) -> str:
    """초를 mm:ss 형식으로 변환"""
    m, s = divmod(int(seconds), 60)
    return f"{m}분 {s}초" if m > 0 else f"{s}초"


def main():
    parser = argparse.ArgumentParser(description="Supabase → Notion 검수 페이지 동기화")
    parser.add_argument("--year", type=int, help="연도 필터 (예: 2026)")
    parser.add_argument("--exam", help="시험 유형 필터 (CSAT, KICE6, KICE9)")
    parser.add_argument("--problem-id", help="단일 문제 ID")
    parser.add_argument("--status", help="상태 필터 (ready, needs_review 등)")
    parser.add_argument("--dry-run", action="store_true", help="미리보기 (Notion 호출 없음)")
    parser.add_argument("--yes", "-y", action="store_true", help="확인 없이 바로 실행")
    args = parser.parse_args()

    # 서비스 초기화
    print("서비스 초기화 중...")
    supabase = SupabaseService()
    notion = NotionService()

    # 문제 목록 조회
    print("Supabase에서 문제 조회 중...")
    if args.problem_id:
        problem = supabase.get_problem(args.problem_id)
        problems = [problem] if problem else []
    else:
        problems = supabase.get_problems_by_filter(
            year=args.year, exam=args.exam, status=args.status
        )

    if not problems:
        print("조회된 문제가 없습니다.")
        return

    # 각 문제에 힌트 조회
    items = []
    for p in problems:
        hints = supabase.get_hints(p["problem_id"])
        items.append({"problem": p, "hints": hints})

    # 통계 미리보기
    with_solution = sum(1 for it in items if it["problem"].get("solution"))
    with_hints = sum(1 for it in items if len(it["hints"]) == 3)
    with_image = sum(1 for it in items if it["problem"].get("problem_image_url"))

    print(f"\n{'='*50}")
    print(f"동기화 대상: {len(items)}문제")
    print(f"  풀이 있음: {with_solution}")
    print(f"  힌트 3단계: {with_hints}")
    print(f"  이미지 있음: {with_image}")
    est_time = len(items) * 10
    print(f"  예상 소요: {format_eta(est_time)}")
    print(f"{'='*50}\n")

    if args.dry_run:
        for it in items:
            p = it["problem"]
            h = it["hints"]
            print(f"  {p['problem_id']}: "
                  f"ans={p.get('answer')}, "
                  f"solution={'Y' if p.get('solution') else 'N'}, "
                  f"hints={len(h)}, "
                  f"image={'Y' if p.get('problem_image_url') else 'N'}")
        print("\n(dry-run 완료 - Notion 호출 없음)")
        return

    # 확인 프롬프트 (단일 문제 또는 --yes 시 생략)
    if not args.yes and not args.problem_id and len(items) > 1:
        answer = input(f"{len(items)}개 문제를 Notion에 동기화합니다. 계속하시겠습니까? (y/N): ")
        if answer.lower() not in ("y", "yes"):
            print("취소되었습니다.")
            return

    # Notion 동기화
    success = 0
    failed = []
    consecutive_failures = 0
    start_time = time.time()

    for i, it in enumerate(items, 1):
        p = it["problem"]
        h = it["hints"]
        pid = p["problem_id"]

        # ETA 계산
        elapsed = time.time() - start_time
        if i > 1:
            avg_per_item = elapsed / (i - 1)
            remaining = avg_per_item * (len(items) - i + 1)
            eta_str = f" (남은 시간: {format_eta(remaining)})"
        else:
            eta_str = ""

        print(f"[{i}/{len(items)}] {pid}{eta_str}", end="")

        try:
            page = notion.create_review_page(p, h)
            page_id = page["id"]

            # notion_page_id를 Supabase에 저장
            if not p.get("notion_page_id"):
                supabase.update_problem(pid, {"notion_page_id": page_id})

            success += 1
            consecutive_failures = 0
            print(f" -> OK ({page_id[:8]}...)")
            time.sleep(1.5)

        except Exception as e:
            failed.append({"id": pid, "error": str(e)})
            consecutive_failures += 1
            print(f" -> FAILED: {e}")

            # Circuit breaker: 5회 연속 실패 시 중단
            if consecutive_failures >= 5:
                print(f"\n연속 {consecutive_failures}회 실패 - 동기화 중단합니다.")
                break

            time.sleep(2)

    # 결과 요약
    total_time = time.time() - start_time
    print(f"\n{'='*50}")
    print(f"동기화 완료: 성공 {success}/{len(items)} ({format_eta(total_time)} 소요)")
    if failed:
        print(f"실패 {len(failed)}개:")
        for item in failed:
            print(f"  - {item['id']}: {item['error']}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
