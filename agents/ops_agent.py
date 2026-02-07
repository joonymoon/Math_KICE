"""
Operations 에이전트 - 통계, 헬스체크, 모니터링
실제 서비스 상태와 데이터 무결성을 확인
"""

import sys
from pathlib import Path
from typing import Optional, Any, Dict, List
from datetime import datetime

from .base import BaseAgent, Task, TaskStatus, AgentMessage

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class OpsAgent(BaseAgent):
    """
    운영 관리 에이전트

    역할:
    - 실제 DB 통계 조회
    - 서비스 헬스체크 (Supabase, Notion, Drive)
    - 데이터 무결성 검증
    - 운영 현황 보고서 생성
    """

    def __init__(self):
        super().__init__(
            name="ops",
            role="운영 관리",
            capabilities=[
                "DB 통계",
                "헬스체크",
                "데이터 무결성",
                "운영 보고서",
                "서비스 모니터링",
            ]
        )
        self._db = None

    def _init_services(self):
        """Supabase 서비스 초기화"""
        from dotenv import load_dotenv
        load_dotenv()
        from src.supabase_service import SupabaseService
        self._db = SupabaseService()
        self.log("운영 서비스 초기화 완료")

    def get_stats(self) -> Dict[str, Any]:
        """
        실제 DB 통계 조회

        Returns:
            통계 딕셔너리 (total, by_status, by_year, by_exam)
        """
        self.ensure_services()
        self.log("DB 통계 조회")

        result = self.safe_execute(self._db.get_stats)
        if not result["success"]:
            return {"success": False, "error": result["error"]}

        return {"success": True, **result["data"]}

    def health_check(self) -> Dict[str, Any]:
        """
        서비스 헬스체크

        Returns:
            각 서비스의 연결 상태
        """
        self.log("서비스 헬스체크 시작")
        checks = {}

        # 1. Supabase 체크
        try:
            from dotenv import load_dotenv
            load_dotenv()
            from src.supabase_service import SupabaseService
            db = SupabaseService()
            stats = db.get_stats()
            checks["supabase"] = {
                "status": "ok",
                "total_problems": stats["total"],
            }
        except Exception as e:
            checks["supabase"] = {"status": "error", "error": str(e)}

        # 2. Notion 체크
        try:
            from src.notion_service import NotionService
            notion = NotionService()
            # 간단한 쿼리로 연결 확인
            notion.client.request(
                path=f"databases/{notion.database_id}",
                method="GET",
            )
            checks["notion"] = {"status": "ok"}
        except Exception as e:
            checks["notion"] = {"status": "error", "error": str(e)}

        # 3. Google Drive 체크
        try:
            from src.google_drive_service import GoogleDriveService
            drive = GoogleDriveService()
            from src.config import GDRIVE_PROBLEMS_FOLDER_ID
            files = drive.list_files(GDRIVE_PROBLEMS_FOLDER_ID)
            checks["google_drive"] = {
                "status": "ok",
                "files_in_problems_folder": len(files),
            }
        except Exception as e:
            checks["google_drive"] = {"status": "error", "error": str(e)}

        # 4. 환경변수 체크
        from src.config import (
            SUPABASE_URL, SUPABASE_KEY, NOTION_TOKEN,
            NOTION_DATABASE_ID, GOOGLE_CLIENT_ID
        )
        env_check = {
            "SUPABASE_URL": bool(SUPABASE_URL),
            "SUPABASE_KEY": bool(SUPABASE_KEY),
            "NOTION_TOKEN": bool(NOTION_TOKEN),
            "NOTION_DATABASE_ID": bool(NOTION_DATABASE_ID),
            "GOOGLE_CLIENT_ID": bool(GOOGLE_CLIENT_ID),
        }
        missing = [k for k, v in env_check.items() if not v]
        checks["env"] = {
            "status": "ok" if not missing else "warning",
            "missing": missing if missing else None,
        }

        # 전체 상태
        all_ok = all(c.get("status") == "ok" for c in checks.values())
        self.log(f"헬스체크 완료: {'ALL OK' if all_ok else 'ISSUES FOUND'}")

        return {
            "success": True,
            "overall": "healthy" if all_ok else "degraded",
            "checks": checks,
            "timestamp": datetime.now().isoformat(),
        }

    def get_problem_report(self, year: Optional[int] = None) -> Dict[str, Any]:
        """
        문제 현황 보고서 생성

        Args:
            year: 연도 필터 (None이면 전체)

        Returns:
            보고서 데이터
        """
        self.ensure_services()
        self.log(f"문제 보고서 생성 (year={year})")

        problems = self._db.get_problems_by_filter(year=year)

        if not problems:
            return {"success": True, "total": 0, "message": "문제 없음"}

        # 상태별 집계
        by_status = {}
        by_exam = {}
        by_score = {}
        with_image = 0
        with_answer = 0
        with_solution = 0

        for p in problems:
            # 상태별
            status = p.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1

            # 시험별
            exam = p.get("exam", "unknown")
            by_exam[exam] = by_exam.get(exam, 0) + 1

            # 배점별
            score = p.get("score") or p.get("score_verified")
            if score:
                by_score[score] = by_score.get(score, 0) + 1

            # 완성도
            if p.get("problem_image_url"):
                with_image += 1
            if p.get("answer") or p.get("answer_verified"):
                with_answer += 1
            if p.get("solution"):
                with_solution += 1

        total = len(problems)
        return {
            "success": True,
            "year": year,
            "total": total,
            "by_status": by_status,
            "by_exam": by_exam,
            "by_score": by_score,
            "completeness": {
                "with_image": with_image,
                "with_answer": with_answer,
                "with_solution": with_solution,
                "image_pct": round(with_image / total * 100, 1) if total else 0,
                "answer_pct": round(with_answer / total * 100, 1) if total else 0,
                "solution_pct": round(with_solution / total * 100, 1) if total else 0,
            },
        }

    def check_data_integrity(self) -> Dict[str, Any]:
        """
        데이터 무결성 검증
        - 이미지 URL 존재 여부
        - 힌트 3개 여부
        - 정답 존재 여부
        - 중복 문제 ID 검사

        Returns:
            무결성 검증 결과
        """
        self.ensure_services()
        self.log("데이터 무결성 검증 시작")

        problems = self._db.get_problems_by_filter()
        issues = []

        seen_ids = set()
        for p in problems:
            pid = p["problem_id"]
            problem_issues = []

            # 중복 검사
            if pid in seen_ids:
                problem_issues.append("중복 problem_id")
            seen_ids.add(pid)

            # 이미지 URL
            img_url = p.get("problem_image_url")
            if not img_url:
                problem_issues.append("이미지 URL 없음")

            # 정답
            if not p.get("answer") and not p.get("answer_verified"):
                problem_issues.append("정답 없음")

            # 배점
            if not p.get("score") and not p.get("score_verified"):
                problem_issues.append("배점 없음")

            # 문항번호 유효성
            q_no = p.get("question_no")
            if q_no and (q_no < 1 or q_no > 30):
                problem_issues.append(f"문항번호 범위 초과: {q_no}")

            # 힌트 검사
            hints = self._db.get_hints(pid)
            if len(hints) < 3:
                problem_issues.append(f"힌트 부족 ({len(hints)}/3)")

            if problem_issues:
                issues.append({"problem_id": pid, "issues": problem_issues})

        # 이슈 유형별 집계
        issue_counts = {}
        for item in issues:
            for issue in item["issues"]:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1

        self.log(f"무결성 검증 완료: {len(problems)}문제 중 {len(issues)}개 이슈")

        return {
            "success": True,
            "total_problems": len(problems),
            "problems_with_issues": len(issues),
            "clean_problems": len(problems) - len(issues),
            "issue_summary": issue_counts,
            "details": issues,
        }

    def print_report(self, year: Optional[int] = None) -> str:
        """보고서를 포맷팅된 문자열로 출력"""
        report = self.get_problem_report(year)
        if not report["success"]:
            return f"보고서 생성 실패: {report.get('error')}"

        lines = []
        lines.append("=" * 55)
        lines.append(f"  KICE 수학 문제 현황 보고서")
        if year:
            lines.append(f"  연도: {year}")
        lines.append("=" * 55)
        lines.append(f"  총 문제 수: {report['total']}")
        lines.append("")

        lines.append("  [상태별]")
        for status, count in report["by_status"].items():
            lines.append(f"    {status}: {count}")

        lines.append("")
        lines.append("  [시험별]")
        for exam, count in report["by_exam"].items():
            lines.append(f"    {exam}: {count}")

        if report["by_score"]:
            lines.append("")
            lines.append("  [배점별]")
            for score, count in sorted(report["by_score"].items()):
                lines.append(f"    {score}점: {count}")

        comp = report["completeness"]
        lines.append("")
        lines.append("  [완성도]")
        lines.append(f"    이미지: {comp['with_image']}/{report['total']} ({comp['image_pct']}%)")
        lines.append(f"    정답:   {comp['with_answer']}/{report['total']} ({comp['answer_pct']}%)")
        lines.append(f"    풀이:   {comp['with_solution']}/{report['total']} ({comp['solution_pct']}%)")
        lines.append("=" * 55)

        return "\n".join(lines)

    def process_task(self, task: Task) -> Any:
        """작업 처리"""
        title = task.title.lower()
        params = task.metadata

        if "stats" in title or "통계" in title:
            return self.get_stats()
        elif "health" in title or "헬스" in title:
            return self.health_check()
        elif "report" in title or "보고" in title:
            return self.get_problem_report(year=params.get("year"))
        elif "integrity" in title or "무결성" in title:
            return self.check_data_integrity()

        return {"error": f"알 수 없는 작업: {task.title}"}

    def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """메시지 처리"""
        if message.message_type == "task_assigned":
            task_data = message.content.get("task", {})
            self.log(f"작업 수신: {task_data.get('title', 'unknown')}")
        return None
