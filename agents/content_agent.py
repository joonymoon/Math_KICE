"""
Content 에이전트 - Notion 동기화 및 콘텐츠 품질 관리
Supabase ↔ Notion 동기화, 데이터 검증, 검수 현황 관리
"""

import sys
import time
from pathlib import Path
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta, timezone

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

    # ──────────────────────────────────────────────
    # 단원별 힌트 템플릿 (score → 3-stage hints)
    # ──────────────────────────────────────────────
    _HINT_BANK: Dict[str, Dict[int, List]] = {
        "지수로그": {
            2: [
                ("concept_direction",
                 "주어진 수를 같은 밑의 거듭제곱으로 나타내세요."),
                ("key_transformation",
                 "밑을 통일한 뒤 지수법칙 $a^m \\cdot a^n = a^{m+n}$을 적용하세요."),
                ("decisive_line",
                 "분수 지수를 통분하여 최종 값을 계산하세요."),
            ],
            3: [
                ("concept_direction",
                 "로그의 밑 변환 공식 $\\log_a b = \\frac{\\log b}{\\log a}$를 활용하세요."),
                ("key_transformation",
                 "로그 성질 $\\log(ab)=\\log a+\\log b$, $\\log a^n = n\\log a$로 정리하세요."),
                ("decisive_line",
                 "정리된 식에 주어진 조건을 대입하여 값을 구하세요."),
            ],
            4: [
                ("concept_direction",
                 "지수함수·로그함수의 그래프 관계를 분석하세요."),
                ("key_transformation",
                 "$t = a^x$ 등 적절한 치환으로 방정식을 변환하세요."),
                ("decisive_line",
                 "치환 변수의 범위 조건에서 해를 결정하세요."),
            ],
        },
        "삼각함수": {
            2: [
                ("concept_direction",
                 "삼각함수의 정의와 특수각의 값을 확인하세요."),
                ("key_transformation",
                 "삼각함수 기본 공식(피타고라스, 배각)을 적용하세요."),
                ("decisive_line",
                 "계산 결과를 선택지와 대조하세요."),
            ],
            3: [
                ("concept_direction",
                 "삼각함수 그래프의 주기·진폭·위상 특성을 파악하세요."),
                ("key_transformation",
                 "삼각함수 합성 $a\\sin x + b\\cos x = \\sqrt{a^2+b^2}\\sin(x+\\alpha)$를 사용하세요."),
                ("decisive_line",
                 "각도 범위 조건에서 최댓값/최솟값을 구하세요."),
            ],
            4: [
                ("concept_direction",
                 "삼각방정식의 근의 개수나 교점 조건을 그래프로 분석하세요."),
                ("key_transformation",
                 "삼각함수의 합성과 역함수 관계를 활용하세요."),
                ("decisive_line",
                 "경우를 나누어 조건을 만족하는 모든 해를 구하세요."),
            ],
        },
        "수열": {
            2: [
                ("concept_direction",
                 "등차수열 또는 등비수열의 일반항 공식을 확인하세요."),
                ("key_transformation",
                 "첫째항과 공차(공비)를 구하여 일반항을 세우세요."),
                ("decisive_line",
                 "일반항에 대입하여 답을 계산하세요."),
            ],
            3: [
                ("concept_direction",
                 "수열의 합 $S_n$과 일반항 $a_n$의 관계: $a_n = S_n - S_{n-1}$를 활용하세요."),
                ("key_transformation",
                 "점화식을 일반항으로 변환하거나, 부분합 관계를 유도하세요."),
                ("decisive_line",
                 "유도된 일반항으로 원하는 값을 계산하세요."),
            ],
            4: [
                ("concept_direction",
                 "점화식의 유형(등차, 등비, 분수, 계차)을 판별하세요."),
                ("key_transformation",
                 "적절한 치환이나 귀납법으로 일반항을 구하세요."),
                ("decisive_line",
                 "조건을 만족하는 자연수를 모두 구하여 답을 결정하세요."),
            ],
        },
        "미분": {
            2: [
                ("concept_direction",
                 "도함수의 정의와 미분 공식을 확인하세요."),
                ("key_transformation",
                 "곱의 미분법 또는 합성함수 미분법을 적용하세요."),
                ("decisive_line",
                 "도함수에 주어진 $x$ 값을 대입하여 답을 구하세요."),
            ],
            3: [
                ("concept_direction",
                 "함수의 극값 조건: $f'(x)=0$이고 $f'$의 부호가 변하는 점을 찾으세요."),
                ("key_transformation",
                 "도함수의 부호 변화를 분석하여 증감표를 그리세요."),
                ("decisive_line",
                 "극값 조건에서 미정계수를 결정하고 답을 구하세요."),
            ],
            4: [
                ("concept_direction",
                 "함수와 도함수의 관계를 그래프적으로 분석하세요."),
                ("key_transformation",
                 "$f'(x)$의 그래프에서 $f(x)$의 극대·극소·변곡점을 파악하세요."),
                ("decisive_line",
                 "조건을 만족하는 함수를 결정하고 요구하는 값을 계산하세요."),
            ],
        },
        "적분": {
            2: [
                ("concept_direction",
                 "부정적분 공식 $\\int x^n dx = \\frac{x^{n+1}}{n+1}+C$를 확인하세요."),
                ("key_transformation",
                 "피적분함수를 전개하거나 간단히 한 뒤 항별로 적분하세요."),
                ("decisive_line",
                 "정적분의 상한·하한을 대입하여 값을 구하세요."),
            ],
            3: [
                ("concept_direction",
                 "정적분과 넓이의 관계, 또는 $\\int_a^b f(x)dx = F(b)-F(a)$를 활용하세요."),
                ("key_transformation",
                 "치환적분 또는 부분적분을 적용하여 적분을 계산하세요."),
                ("decisive_line",
                 "계산된 적분값에서 답을 도출하세요."),
            ],
            4: [
                ("concept_direction",
                 "정적분으로 정의된 함수의 성질을 분석하세요."),
                ("key_transformation",
                 "$\\frac{d}{dx}\\int_a^x f(t)dt = f(x)$ 등 미적분 기본정리를 적용하세요."),
                ("decisive_line",
                 "함수 관계를 풀어 조건을 만족하는 답을 구하세요."),
            ],
        },
        "함수의극한연속": {
            2: [
                ("concept_direction",
                 "함수의 극한 정의와 극한값 계산법을 확인하세요."),
                ("key_transformation",
                 "대입법, 인수분해, 또는 유리화를 통해 극한을 계산하세요."),
                ("decisive_line",
                 "계산 결과에서 답을 고르세요."),
            ],
            3: [
                ("concept_direction",
                 "연속 조건: $\\lim_{x \\to a}f(x) = f(a)$를 확인하세요."),
                ("key_transformation",
                 "좌극한 = 우극한 = 함수값 조건을 연립하세요."),
                ("decisive_line",
                 "미정계수를 결정하여 답을 구하세요."),
            ],
            4: [
                ("concept_direction",
                 "구간별 정의된 함수의 연속성과 미분가능성을 분석하세요."),
                ("key_transformation",
                 "경계점에서 좌미분 = 우미분 조건을 추가로 적용하세요."),
                ("decisive_line",
                 "모든 조건을 연립하여 미정계수와 답을 결정하세요."),
            ],
        },
    }

    _SOLUTION_TEMPLATES: Dict[str, str] = {
        "지수로그": (
            "지수·로그 성질 활용<br><br>"
            "주어진 식에서 밑을 통일하고 지수법칙을 적용합니다.<br>"
            "지수법칙: $a^m \\cdot a^n = a^{{m+n}}$, $(a^m)^n = a^{{mn}}$<br>"
            "로그법칙: $\\log_a(bc) = \\log_a b + \\log_a c$<br><br>"
            "정답: {answer}"
        ),
        "삼각함수": (
            "삼각함수 공식 활용<br><br>"
            "삼각함수의 정의와 공식을 적용하여 풀이합니다.<br>"
            "활용 공식: 배각, 반각, 합차, 합성 공식<br><br>"
            "정답: {answer}"
        ),
        "수열": (
            "수열 공식 활용<br><br>"
            "수열의 일반항과 합의 관계를 이용하여 풀이합니다.<br>"
            "핵심: $a_n = S_n - S_{{n-1}}$ (단, $n \\geq 2$)<br><br>"
            "정답: {answer}"
        ),
        "미분": (
            "미분법 활용<br><br>"
            "도함수를 구하고 주어진 조건을 적용합니다.<br>"
            "핵심: 극값 조건 $f'(x) = 0$, 증감표 분석<br><br>"
            "정답: {answer}"
        ),
        "적분": (
            "적분법 활용<br><br>"
            "피적분함수를 정리하고 적분을 계산합니다.<br>"
            "핵심: $\\int_a^b f(x)dx = F(b) - F(a)$<br><br>"
            "정답: {answer}"
        ),
        "함수의극한연속": (
            "함수의 극한과 연속성 활용<br><br>"
            "극한값을 계산하거나 연속 조건을 적용합니다.<br>"
            "핵심: $\\lim_{{x \\to a}}f(x) = f(a)$ (연속)<br><br>"
            "정답: {answer}"
        ),
    }

    def fill_missing_content(
        self,
        year: Optional[int] = None,
        exam: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        미완성 문제의 힌트(3단계)와 풀이를 자동 생성

        단원(unit)·배점(score)별 맞춤 힌트와 풀이 프레임워크를 생성합니다.

        Args:
            year: 연도 필터
            exam: 시험 유형 필터
            dry_run: True면 미리보기만 (DB 변경 없음)

        Returns:
            채우기 결과
        """
        self.ensure_services()
        self.status = "working"
        self.log(f"미완성 콘텐츠 채우기 시작 (year={year}, exam={exam}, dry_run={dry_run})")

        # 1) 미완성 문제 파악
        validation = self.validate_problems(year=year, exam=exam)
        incomplete = validation.get("incomplete_items", [])

        if not incomplete:
            self.status = "idle"
            return {"success": True, "filled": 0, "message": "모든 문제가 이미 완성되어 있습니다."}

        # 2) 채울 대상 분석
        targets = []
        for item in incomplete:
            pid = item["problem_id"]
            issues = item["issues"]
            needs_hints = any("힌트" in i for i in issues)
            needs_solution = "풀이 없음" in issues

            if needs_hints or needs_solution:
                problem = self._db.get_problem(pid)
                targets.append({
                    "problem": problem,
                    "needs_hints": needs_hints,
                    "needs_solution": needs_solution,
                })

        if not targets:
            self.status = "idle"
            return {"success": True, "filled": 0, "message": "힌트/풀이 누락 없음"}

        # dry_run 미리보기
        if dry_run:
            preview = []
            for t in targets:
                p = t["problem"]
                unit = p.get("unit", "")
                score = p.get("score", 3)
                preview.append({
                    "problem_id": p["problem_id"],
                    "unit": unit,
                    "score": score,
                    "fill_hints": t["needs_hints"],
                    "fill_solution": t["needs_solution"],
                })
            self.status = "idle"
            return {
                "success": True,
                "dry_run": True,
                "targets": len(targets),
                "preview": preview,
            }

        # 3) 콘텐츠 생성 및 저장
        filled = 0
        errors = []

        for t in targets:
            p = t["problem"]
            pid = p["problem_id"]
            unit = p.get("unit", "")
            score = p.get("score", 3)
            answer = p.get("answer", "?")
            answer_type = p.get("answer_type", "multiple")

            # 정답 포맷팅
            if answer_type == "multiple":
                formatted_answer = f"{answer}번" if answer else "?"
            else:
                formatted_answer = f"$\\boxed{{{answer}}}$" if answer else "?"

            self.log(f"  {pid} ({unit}, {score}점) 콘텐츠 생성 중...")

            try:
                # 힌트 생성
                if t["needs_hints"]:
                    hint_bank = self._HINT_BANK.get(unit, {})
                    # 해당 배점이 없으면 가장 가까운 배점
                    hints = hint_bank.get(score) or hint_bank.get(3) or hint_bank.get(2)

                    if hints:
                        for stage, (hint_type, hint_text) in enumerate(hints, 1):
                            self._db.create_hint(pid, stage, hint_type, hint_text)
                    else:
                        # fallback: 범용 힌트
                        self._db.create_hint(pid, 1, "concept_direction",
                            "문제에서 요구하는 핵심 개념을 파악하세요.")
                        self._db.create_hint(pid, 2, "key_transformation",
                            "조건을 수식으로 변환하고 핵심 공식을 적용하세요.")
                        self._db.create_hint(pid, 3, "decisive_line",
                            "정리된 식에서 답을 계산하세요.")

                # 풀이 생성
                if t["needs_solution"]:
                    template = self._SOLUTION_TEMPLATES.get(unit, (
                        "풀이<br><br>"
                        "주어진 조건을 정리하고 핵심 공식을 적용합니다.<br><br>"
                        "정답: {answer}"
                    ))
                    solution_text = template.format(answer=formatted_answer)
                    self._db.update_problem(pid, {"solution": solution_text})

                filled += 1

            except Exception as e:
                errors.append({"problem_id": pid, "error": str(e)[:200]})
                self.log(f"  오류: {pid} - {e}")

        self.status = "idle"
        self.log(f"콘텐츠 채우기 완료: {filled}개 처리, {len(errors)}개 오류")

        return {
            "success": True,
            "filled": filled,
            "errors_count": len(errors),
            "total_targets": len(targets),
            "errors": errors if errors else None,
        }

    def set_publish_schedule(
        self,
        year: Optional[int] = None,
        exam: Optional[str] = None,
        problem_id: Optional[str] = None,
        interval_hours: int = 24,
        published_at: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        문제 공개 스케줄 설정 (시간차 힌트 공개)

        Args:
            year: 연도 필터
            exam: 시험 유형 필터
            problem_id: 단일 문제 ID
            interval_hours: 힌트 단계 간 간격 (시간, 기본 24)
            published_at: 공개 시각 (ISO format, None이면 현재 시각)
            dry_run: True면 미리보기만

        Returns:
            스케줄 설정 결과
        """
        self.ensure_services()
        self.status = "working"
        self.log(f"공개 스케줄 설정 (year={year}, exam={exam}, interval={interval_hours}h)")

        # 대상 문제 조회
        if problem_id:
            problem = self._db.get_problem(problem_id)
            problems = [problem] if problem else []
        else:
            problems = self._db.get_problems_by_filter(year=year, exam=exam)

        if not problems:
            self.status = "idle"
            return {"success": True, "updated": 0, "message": "대상 문제 없음"}

        # 공개 시각 결정
        if published_at:
            pub_time = datetime.fromisoformat(published_at)
            if pub_time.tzinfo is None:
                pub_time = pub_time.replace(tzinfo=timezone.utc)
        else:
            pub_time = datetime.now(timezone.utc)

        if dry_run:
            preview = []
            for p in problems:
                pid = p["problem_id"]
                preview.append({
                    "problem_id": pid,
                    "published_at": pub_time.isoformat(),
                    "hint_interval_hours": interval_hours,
                    "hint1_at": pub_time.isoformat(),
                    "hint2_at": (pub_time + timedelta(hours=interval_hours)).isoformat(),
                    "hint3_solution_at": (pub_time + timedelta(hours=interval_hours * 2)).isoformat(),
                })
            self.status = "idle"
            return {
                "success": True,
                "dry_run": True,
                "targets": len(preview),
                "preview": preview,
            }

        # 실제 업데이트
        updated = 0
        errors = []
        for p in problems:
            pid = p["problem_id"]
            try:
                self._db.client.table("problems").update({
                    "published_at": pub_time.isoformat(),
                    "hint_interval_hours": interval_hours,
                }).eq("problem_id", pid).execute()
                updated += 1
            except Exception as e:
                errors.append({"problem_id": pid, "error": str(e)[:200]})

        self.status = "idle"
        self.log(f"스케줄 설정 완료: {updated}개, 오류 {len(errors)}개")

        return {
            "success": True,
            "updated": updated,
            "errors_count": len(errors),
            "total": len(problems),
            "published_at": pub_time.isoformat(),
            "hint_interval_hours": interval_hours,
            "schedule": {
                "hint1": pub_time.isoformat(),
                "hint2": (pub_time + timedelta(hours=interval_hours)).isoformat(),
                "hint3_solution": (pub_time + timedelta(hours=interval_hours * 2)).isoformat(),
            },
            "errors": errors if errors else None,
        }

    def get_publish_schedule(
        self,
        year: Optional[int] = None,
        exam: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        문제 공개 스케줄 조회

        Returns:
            스케줄 현황
        """
        self.ensure_services()
        self.log(f"공개 스케줄 조회 (year={year}, exam={exam})")

        problems = self._db.get_problems_by_filter(year=year, exam=exam)

        scheduled = []
        unscheduled = []
        for p in problems:
            pid = p["problem_id"]
            pub = p.get("published_at")
            if pub:
                interval = p.get("hint_interval_hours", 24) or 24
                if isinstance(pub, str):
                    pub_dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                else:
                    pub_dt = pub
                scheduled.append({
                    "problem_id": pid,
                    "published_at": pub_dt.isoformat(),
                    "hint_interval_hours": interval,
                    "hint2_at": (pub_dt + timedelta(hours=interval)).isoformat(),
                    "hint3_at": (pub_dt + timedelta(hours=interval * 2)).isoformat(),
                })
            else:
                unscheduled.append(pid)

        return {
            "success": True,
            "total": len(problems),
            "scheduled": len(scheduled),
            "unscheduled": len(unscheduled),
            "schedule_items": scheduled,
            "unscheduled_ids": unscheduled,
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
        elif "fill" in title or "채우기" in title:
            return self.fill_missing_content(
                year=params.get("year"),
                exam=params.get("exam"),
                dry_run=params.get("dry_run", False),
            )
        elif "schedule" in title or "스케줄" in title or "공개" in title:
            if "set" in title or "설정" in title:
                return self.set_publish_schedule(
                    year=params.get("year"),
                    exam=params.get("exam"),
                    problem_id=params.get("problem_id"),
                    interval_hours=params.get("interval_hours", 24),
                    published_at=params.get("published_at"),
                    dry_run=params.get("dry_run", False),
                )
            return self.get_publish_schedule(
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
