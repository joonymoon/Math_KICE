"""
Content 에이전트 - Notion 동기화 및 콘텐츠 품질 관리
Supabase ↔ Notion 동기화, 데이터 검증, 검수 현황 관리
"""

import sys
import time
from pathlib import Path
from typing import Optional, Any, Dict, List
from datetime import datetime

from .base import BaseAgent, Task, TaskStatus, AgentMessage

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class ContentAgent(BaseAgent):
    """
    콘텐츠 관리 에이전트

    역할:
    - Supabase → Notion 검수 페이지 동기화
    - Notion → Supabase 검수 결과 동기화
    - 문제 데이터 완성도 검증
    - 검수 현황 보고
    """

    def __init__(self):
        super().__init__(
            name="content",
            role="콘텐츠 관리",
            capabilities=[
                "Notion 동기화",
                "검수 페이지 생성",
                "데이터 검증",
                "콘텐츠 품질 관리",
                "검수 현황 보고",
            ]
        )
        self._db = None
        self._notion = None

    def _init_services(self):
        """Supabase, Notion 서비스 초기화"""
        from dotenv import load_dotenv
        load_dotenv()
        from src.supabase_service import SupabaseService
        from src.notion_service import NotionService
        self._db = SupabaseService()
        self._notion = NotionService()
        self.log("콘텐츠 서비스 초기화 완료")

    def sync_to_notion(
        self,
        year: Optional[int] = None,
        exam: Optional[str] = None,
        status: Optional[str] = None,
        problem_id: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Supabase → Notion 검수 페이지 동기화

        Args:
            year: 연도 필터
            exam: 시험 유형 필터
            status: 상태 필터
            problem_id: 단일 문제 ID
            dry_run: True면 미리보기만

        Returns:
            동기화 결과
        """
        self.ensure_services()
        self.status = "working"
        self.log(f"Notion 동기화 시작 (year={year}, exam={exam}, dry_run={dry_run})")

        # 문제 목록 조회
        if problem_id:
            problem = self._db.get_problem(problem_id)
            problems = [problem] if problem else []
        else:
            problems = self._db.get_problems_by_filter(
                year=year, exam=exam, status=status
            )

        if not problems:
            self.status = "idle"
            return {"success": True, "synced": 0, "total": 0, "message": "동기화 대상 없음"}

        # 힌트 포함 아이템 구성
        items = []
        for p in problems:
            hints = self._db.get_hints(p["problem_id"])
            items.append({"problem": p, "hints": hints})

        # 통계
        with_solution = sum(1 for it in items if it["problem"].get("solution"))
        with_hints = sum(1 for it in items if len(it["hints"]) == 3)
        with_image = sum(1 for it in items if it["problem"].get("problem_image_url"))

        summary = {
            "total": len(items),
            "with_solution": with_solution,
            "with_hints_3": with_hints,
            "with_image": with_image,
        }

        if dry_run:
            preview = []
            for it in items:
                p = it["problem"]
                preview.append({
                    "problem_id": p["problem_id"],
                    "answer": p.get("answer"),
                    "has_solution": bool(p.get("solution")),
                    "hints": len(it["hints"]),
                    "has_image": bool(p.get("problem_image_url")),
                })
            self.status = "idle"
            return {"success": True, "dry_run": True, "summary": summary, "problems": preview}

        # 실제 동기화 실행
        success_count = 0
        failed = []
        consecutive_failures = 0

        for i, it in enumerate(items, 1):
            p = it["problem"]
            h = it["hints"]
            pid = p["problem_id"]

            self.log(f"[{i}/{len(items)}] {pid} 동기화 중...")

            try:
                page = self._notion.create_review_page(p, h)
                page_id = page["id"]

                # notion_page_id 저장
                if not p.get("notion_page_id"):
                    self._db.update_problem(pid, {"notion_page_id": page_id})

                success_count += 1
                consecutive_failures = 0
                time.sleep(1.5)  # Notion rate limit

            except Exception as e:
                failed.append({"id": pid, "error": str(e)})
                consecutive_failures += 1
                self.log(f"  실패: {pid} - {e}")

                if consecutive_failures >= 5:
                    self.log("연속 5회 실패 - 동기화 중단")
                    break
                time.sleep(2)

        self.status = "idle"
        return {
            "success": True,
            "synced": success_count,
            "failed": len(failed),
            "total": len(items),
            "summary": summary,
            "errors": failed if failed else None,
        }

    def sync_from_notion(self) -> Dict[str, Any]:
        """
        Notion → Supabase 검수 결과 동기화
        검수 완료된 문제를 Supabase에 반영

        Returns:
            동기화 결과
        """
        self.ensure_services()
        self.status = "working"
        self.log("Notion → Supabase 동기화 시작")

        result = self.safe_execute(self._notion.sync_to_supabase, self._db)

        self.status = "idle"
        if result["success"]:
            synced = result["data"] or []
            self.log(f"Notion → Supabase 동기화 완료: {len(synced)}개")
            return {"success": True, "synced": len(synced), "problems": synced}
        else:
            return {"success": False, "error": result["error"]}

    def validate_problems(
        self,
        year: Optional[int] = None,
        exam: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        문제 데이터 완성도 검증

        Args:
            year: 연도 필터
            exam: 시험 유형 필터

        Returns:
            검증 결과 (complete, incomplete, issues)
        """
        self.ensure_services()
        self.status = "working"
        self.log(f"데이터 검증 시작 (year={year}, exam={exam})")

        problems = self._db.get_problems_by_filter(year=year, exam=exam)

        complete = []
        incomplete = []
        issues = []

        for p in problems:
            pid = p["problem_id"]
            hints = self._db.get_hints(pid)
            problems_list = []

            # 필수 필드 검증
            if not p.get("problem_image_url"):
                problems_list.append("이미지 없음")
            if not p.get("answer") and not p.get("answer_verified"):
                problems_list.append("정답 없음")
            if not p.get("score") and not p.get("score_verified"):
                problems_list.append("배점 없음")
            if len(hints) < 3:
                problems_list.append(f"힌트 {len(hints)}/3개")
            if not p.get("solution"):
                problems_list.append("풀이 없음")
            if not p.get("subject"):
                problems_list.append("과목 미분류")
            if not p.get("unit"):
                problems_list.append("단원 미분류")

            if problems_list:
                incomplete.append({"problem_id": pid, "issues": problems_list})
            else:
                complete.append(pid)

        # 상태별 이슈 집계
        issue_counts = {}
        for item in incomplete:
            for issue in item["issues"]:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1

        self.status = "idle"
        self.log(f"검증 완료: 완전 {len(complete)}, 불완전 {len(incomplete)}")

        return {
            "success": True,
            "total": len(problems),
            "complete": len(complete),
            "incomplete": len(incomplete),
            "complete_ids": complete,
            "incomplete_items": incomplete,
            "issue_summary": issue_counts,
        }

    def get_review_status(self) -> Dict[str, Any]:
        """
        검수 현황 보고

        Returns:
            상태별 문제 수
        """
        self.ensure_services()
        self.log("검수 현황 조회")

        stats_result = self.safe_execute(self._db.get_stats)
        if not stats_result["success"]:
            return {"success": False, "error": stats_result["error"]}

        stats = stats_result["data"]
        return {
            "success": True,
            "total": stats["total"],
            "by_status": stats["by_status"],
            "needs_review": stats["by_status"].get("needs_review", 0),
            "ready": stats["by_status"].get("ready", 0),
            "hold": stats["by_status"].get("hold", 0),
        }

    def process_task(self, task: Task) -> Any:
        """작업 처리"""
        title = task.title.lower()
        params = task.metadata

        if "notion" in title and ("sync" in title or "동기화" in title):
            if "from" in title or "supabase" in title.split("→")[0] if "→" in title else False:
                return self.sync_from_notion()
            return self.sync_to_notion(
                year=params.get("year"),
                exam=params.get("exam"),
                dry_run=params.get("dry_run", False),
            )
        elif "validate" in title or "검증" in title:
            return self.validate_problems(
                year=params.get("year"),
                exam=params.get("exam"),
            )
        elif "review" in title or "검수" in title:
            return self.get_review_status()

        return {"error": f"알 수 없는 작업: {task.title}"}

    def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """메시지 처리"""
        if message.message_type == "task_assigned":
            task_data = message.content.get("task", {})
            self.log(f"작업 수신: {task_data.get('title', 'unknown')}")
        return None
