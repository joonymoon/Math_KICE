"""
KICE 수학 문제 관리 시스템
- 22~25년 수능/평가원 수1·수2 공통 3·4점 문제
- Supabase 연동
- 오늘의 문제 자동 발송 + 30분 후 힌트 활성화
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class MathProblemService:
    """수학 문제 관리 서비스"""

    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(url, key)
        self.default_hint_delay_minutes = 30

    # ============================================
    # 문제 관련
    # ============================================

    def get_problem(self, problem_id: str) -> dict:
        """문제 조회 (메타데이터만, 원문 텍스트 없음)"""
        response = self.supabase.table("problems") \
            .select("*") \
            .eq("problem_id", problem_id) \
            .eq("status", "ready") \
            .single() \
            .execute()
        return response.data

    def get_problems_by_filter(
        self,
        year: Optional[int] = None,
        exam_type: Optional[str] = None,  # CSAT, KICE6, KICE9
        subject: Optional[str] = None,    # Math1, Math2
        unit: Optional[str] = None,
        score: Optional[int] = None       # 3 or 4
    ) -> list:
        """조건별 문제 목록 조회"""
        query = self.supabase.table("problems") \
            .select("*") \
            .eq("status", "ready")

        if year:
            query = query.eq("year", year)
        if exam_type:
            query = query.eq("exam_type", exam_type)
        if subject:
            query = query.eq("subject", subject)
        if unit:
            query = query.eq("unit", unit)
        if score:
            query = query.eq("score", score)

        response = query.order("year", desc=True) \
            .order("exam_type") \
            .order("question_no") \
            .execute()
        return response.data

    def select_daily_problem(self, user_id: str) -> Optional[str]:
        """오늘의 문제 선정 (아직 풀지 않은 문제 중 랜덤)"""
        # 이미 풀었거나 발송된 문제 ID 조회
        delivered = self.supabase.table("deliveries") \
            .select("problem_id") \
            .eq("user_id", user_id) \
            .execute()

        delivered_ids = [d["problem_id"] for d in delivered.data]

        # 발송되지 않은 문제 중 랜덤 선택
        query = self.supabase.table("problems") \
            .select("problem_id") \
            .eq("status", "ready")

        if delivered_ids:
            query = query.not_.in_("problem_id", delivered_ids)

        response = query.limit(1).execute()

        if response.data:
            return response.data[0]["problem_id"]
        return None

    # ============================================
    # 힌트 관련
    # ============================================

    def get_hints(self, problem_id: str) -> list:
        """문제의 3단계 힌트 조회"""
        response = self.supabase.table("hints") \
            .select("*") \
            .eq("problem_id", problem_id) \
            .order("stage") \
            .execute()
        return response.data

    def can_view_hint(self, delivery_id: str, stage: int) -> dict:
        """힌트 조회 가능 여부 확인"""
        delivery = self.supabase.table("deliveries") \
            .select("hint_available_at, hint_1_viewed_at, hint_2_viewed_at") \
            .eq("id", delivery_id) \
            .single() \
            .execute()

        data = delivery.data
        now = datetime.now()
        hint_available = datetime.fromisoformat(data["hint_available_at"].replace("Z", "+00:00"))

        # 아직 힌트 활성화 시간이 안 됐으면
        if now < hint_available.replace(tzinfo=None):
            remaining = (hint_available.replace(tzinfo=None) - now).seconds
            return {
                "can_view": False,
                "reason": "time_not_reached",
                "remaining_seconds": remaining,
                "message": f"힌트 활성화까지 {remaining // 60}분 {remaining % 60}초 남았습니다."
            }

        # 이전 단계 힌트 확인
        if stage == 1:
            return {"can_view": True}
        elif stage == 2:
            if not data.get("hint_1_viewed_at"):
                return {
                    "can_view": False,
                    "reason": "previous_hint_not_viewed",
                    "message": "힌트 ①을 먼저 확인해주세요."
                }
            return {"can_view": True}
        elif stage == 3:
            if not data.get("hint_2_viewed_at"):
                return {
                    "can_view": False,
                    "reason": "previous_hint_not_viewed",
                    "message": "힌트 ②를 먼저 확인해주세요."
                }
            return {"can_view": True}

        return {"can_view": False, "reason": "invalid_stage"}

    def view_hint(self, delivery_id: str, stage: int) -> dict:
        """힌트 조회 (조회 기록 저장)"""
        # 조회 가능 여부 확인
        check = self.can_view_hint(delivery_id, stage)
        if not check["can_view"]:
            return check

        # 배달 정보 조회
        delivery = self.supabase.table("deliveries") \
            .select("problem_id") \
            .eq("id", delivery_id) \
            .single() \
            .execute()

        problem_id = delivery.data["problem_id"]

        # 힌트 내용 조회
        hint = self.supabase.table("hints") \
            .select("*") \
            .eq("problem_id", problem_id) \
            .eq("stage", stage) \
            .single() \
            .execute()

        # 조회 기록 저장
        field = f"hint_{stage}_viewed_at"
        self.supabase.table("deliveries") \
            .update({field: datetime.now().isoformat()}) \
            .eq("id", delivery_id) \
            .execute()

        # 힌트 요청 로그 저장
        self.supabase.table("hint_requests").insert({
            "delivery_id": delivery_id,
            "stage": stage,
            "requested_at": datetime.now().isoformat(),
            "was_available": True
        }).execute()

        return {
            "can_view": True,
            "hint": hint.data
        }

    # ============================================
    # 발송 관련
    # ============================================

    def deliver_problem(
        self,
        user_id: str,
        problem_id: str,
        method: str = "push"
    ) -> dict:
        """문제 발송"""
        now = datetime.now()

        # 사용자 설정 조회
        user = self.supabase.table("users") \
            .select("hint_delay_minutes") \
            .eq("id", user_id) \
            .single() \
            .execute()

        delay = user.data.get("hint_delay_minutes", self.default_hint_delay_minutes)
        hint_available_at = now + timedelta(minutes=delay)

        # 발송 기록 생성
        delivery = self.supabase.table("deliveries").insert({
            "user_id": user_id,
            "problem_id": problem_id,
            "delivered_at": now.isoformat(),
            "delivery_method": method,
            "hint_available_at": hint_available_at.isoformat(),
            "status": "pending"
        }).execute()

        return {
            "delivery_id": delivery.data[0]["id"],
            "problem_id": problem_id,
            "delivered_at": now.isoformat(),
            "hint_available_at": hint_available_at.isoformat(),
            "hint_delay_minutes": delay
        }

    def submit_answer(
        self,
        delivery_id: str,
        user_answer: str
    ) -> dict:
        """답안 제출"""
        # 배달 정보 조회
        delivery = self.supabase.table("deliveries") \
            .select("problem_id, delivered_at") \
            .eq("id", delivery_id) \
            .single() \
            .execute()

        problem_id = delivery.data["problem_id"]
        delivered_at = datetime.fromisoformat(
            delivery.data["delivered_at"].replace("Z", "+00:00")
        )

        # 정답 조회
        problem = self.supabase.table("problems") \
            .select("answer") \
            .eq("problem_id", problem_id) \
            .single() \
            .execute()

        correct_answer = problem.data["answer"]
        is_correct = user_answer.strip() == correct_answer.strip()

        now = datetime.now()
        time_spent = int((now - delivered_at.replace(tzinfo=None)).total_seconds())

        # 제출 기록 업데이트
        self.supabase.table("deliveries").update({
            "user_answer": user_answer,
            "answered_at": now.isoformat(),
            "is_correct": is_correct,
            "time_spent_seconds": time_spent,
            "status": "answered"
        }).eq("id", delivery_id).execute()

        return {
            "is_correct": is_correct,
            "correct_answer": correct_answer if not is_correct else None,
            "time_spent_seconds": time_spent
        }

    # ============================================
    # 일일 스케줄 관련
    # ============================================

    def schedule_daily_problems(self, target_date: str = None) -> list:
        """일일 문제 스케줄 생성 (모든 활성 사용자 대상)"""
        if not target_date:
            target_date = datetime.now().strftime("%Y-%m-%d")

        # 활성 사용자 조회
        users = self.supabase.table("users") \
            .select("id, preferred_time, daily_problem_count") \
            .execute()

        scheduled = []

        for user in users.data:
            user_id = user["id"]
            preferred_time = user.get("preferred_time", "07:00")

            # 이미 스케줄된 경우 스킵
            existing = self.supabase.table("daily_schedules") \
                .select("id") \
                .eq("scheduled_date", target_date) \
                .eq("user_id", user_id) \
                .execute()

            if existing.data:
                continue

            # 문제 선정
            problem_id = self.select_daily_problem(user_id)
            if not problem_id:
                continue

            # 스케줄 생성
            schedule = self.supabase.table("daily_schedules").insert({
                "scheduled_date": target_date,
                "user_id": user_id,
                "problem_id": problem_id,
                "scheduled_time": preferred_time,
                "status": "scheduled"
            }).execute()

            scheduled.append(schedule.data[0])

        return scheduled

    def execute_scheduled_deliveries(self) -> list:
        """스케줄된 발송 실행"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_date = now.strftime("%Y-%m-%d")

        # 오늘 날짜, 현재 시간 이전에 스케줄되고 아직 발송 안 된 것들
        schedules = self.supabase.table("daily_schedules") \
            .select("*") \
            .eq("scheduled_date", current_date) \
            .eq("status", "scheduled") \
            .lte("scheduled_time", current_time) \
            .execute()

        executed = []

        for schedule in schedules.data:
            try:
                # 발송 실행
                delivery = self.deliver_problem(
                    user_id=schedule["user_id"],
                    problem_id=schedule["problem_id"],
                    method="push"
                )

                # 스케줄 상태 업데이트
                self.supabase.table("daily_schedules").update({
                    "status": "sent",
                    "executed_at": now.isoformat()
                }).eq("id", schedule["id"]).execute()

                executed.append({
                    "schedule_id": schedule["id"],
                    "delivery": delivery
                })

            except Exception as e:
                # 실패 기록
                self.supabase.table("daily_schedules").update({
                    "status": "failed",
                    "error_message": str(e)
                }).eq("id", schedule["id"]).execute()

        return executed


# ============================================
# Notion 연동 유틸리티
# ============================================

class NotionSync:
    """Notion 검수 대시보드 연동"""

    def __init__(self, notion_token: str, database_id: str):
        self.token = notion_token
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Bearer {notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    def create_review_card(self, problem: dict) -> dict:
        """검수용 Notion 카드 생성"""
        import requests

        properties = {
            "문제 ID": {"title": [{"text": {"content": problem["problem_id"]}}]},
            "연도": {"number": problem["year"]},
            "시험": {"select": {"name": problem["exam_type"]}},
            "문항번호": {"number": problem["question_no"]},
            "과목": {"select": {"name": problem["subject"]}},
            "단원": {"select": {"name": problem["unit"]}},
            "배점": {"number": problem["score"]},
            "정답": {"rich_text": [{"text": {"content": problem["answer"]}}]},
            "출제의도": {"rich_text": [{"text": {"content": problem["intent_summary"]}}]},
            "상태": {"select": {"name": "Needs Review"}},
            "신뢰도": {"number": problem.get("confidence_score", 0)},
            "원본링크": {"url": problem.get("source_pdf_url", "")}
        }

        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=self.headers,
            json={
                "parent": {"database_id": self.database_id},
                "properties": properties
            }
        )

        return response.json()

    def get_ready_problems(self) -> list:
        """검수 완료된 문제 목록 조회"""
        import requests

        response = requests.post(
            f"https://api.notion.com/v1/databases/{self.database_id}/query",
            headers=self.headers,
            json={
                "filter": {
                    "property": "상태",
                    "select": {"equals": "Ready"}
                }
            }
        )

        return response.json().get("results", [])


# ============================================
# 예시 사용법
# ============================================

def example_usage():
    """사용 예시"""
    service = MathProblemService()

    # 1. 조건별 문제 조회
    problems = service.get_problems_by_filter(
        year=2024,
        subject="Math2",
        score=4
    )
    print(f"2024년 수2 4점 문제: {len(problems)}개")

    # 2. 문제 발송
    user_id = "example-user-uuid"
    problem_id = service.select_daily_problem(user_id)
    if problem_id:
        delivery = service.deliver_problem(user_id, problem_id)
        print(f"발송 완료: {delivery}")

        # 3. 힌트 조회 시도
        delivery_id = delivery["delivery_id"]

        # 30분 후 힌트 1 조회
        hint_check = service.can_view_hint(delivery_id, stage=1)
        if hint_check["can_view"]:
            hint = service.view_hint(delivery_id, stage=1)
            print(f"힌트 1: {hint['hint']['hint_text']}")
        else:
            print(f"힌트 불가: {hint_check['message']}")

        # 4. 답안 제출
        result = service.submit_answer(delivery_id, "3")
        if result["is_correct"]:
            print("정답입니다!")
        else:
            print(f"오답입니다. 정답: {result['correct_answer']}")


if __name__ == "__main__":
    example_usage()
