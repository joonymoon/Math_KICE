"""
Business 에이전트 - 비즈니스 담당
요금제, 결제, 마케팅
"""

from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from .base import BaseAgent, Task, TaskStatus, AgentMessage


class BusinessAgent(BaseAgent):
    """
    비즈니스 에이전트

    역할:
    - 요금제 설계 및 관리
    - 결제 시스템 기획
    - 마케팅 전략 수립
    - 수익 분석
    - 사용자 분석
    """

    def __init__(self):
        super().__init__(
            name="business",
            role="비즈니스",
            capabilities=[
                "요금제 설계",
                "결제 시스템",
                "마케팅 전략",
                "수익 분석",
                "사용자 분석",
                "경쟁사 분석",
            ]
        )
        self.pricing_plans: List[Dict] = []
        self.marketing_campaigns: List[Dict] = []
        self.revenue_data: Dict[str, Any] = {}
        self.user_analytics: Dict[str, Any] = {}

    def design_pricing_plans(self) -> List[Dict[str, Any]]:
        """요금제 설계"""
        self.log("요금제 설계")

        plans = [
            {
                "id": "free",
                "name": "무료 체험",
                "price": 0,
                "billing_cycle": None,
                "features": [
                    {"name": "일일 문제 1개", "included": True},
                    {"name": "기본 힌트 제공", "included": True},
                    {"name": "풀이 보기", "included": False},
                    {"name": "오답노트", "included": False},
                    {"name": "학습 분석", "included": False},
                    {"name": "광고 제거", "included": False},
                ],
                "limits": {
                    "daily_problems": 1,
                    "hint_delay_minutes": 60,
                    "history_days": 7,
                },
                "target_audience": "체험 사용자",
            },
            {
                "id": "basic",
                "name": "베이직",
                "price": 9900,
                "billing_cycle": "monthly",
                "features": [
                    {"name": "일일 문제 3개", "included": True},
                    {"name": "기본 힌트 제공", "included": True},
                    {"name": "풀이 보기", "included": True},
                    {"name": "오답노트", "included": True},
                    {"name": "학습 분석", "included": False},
                    {"name": "광고 제거", "included": True},
                ],
                "limits": {
                    "daily_problems": 3,
                    "hint_delay_minutes": 30,
                    "history_days": 30,
                },
                "target_audience": "일반 학습자",
            },
            {
                "id": "premium",
                "name": "프리미엄",
                "price": 19900,
                "billing_cycle": "monthly",
                "features": [
                    {"name": "무제한 문제", "included": True},
                    {"name": "즉시 힌트", "included": True},
                    {"name": "풀이 보기", "included": True},
                    {"name": "오답노트", "included": True},
                    {"name": "학습 분석", "included": True},
                    {"name": "광고 제거", "included": True},
                    {"name": "1:1 질문 (월 5회)", "included": True},
                ],
                "limits": {
                    "daily_problems": -1,  # 무제한
                    "hint_delay_minutes": 0,  # 즉시
                    "history_days": -1,  # 무제한
                    "questions_per_month": 5,
                },
                "target_audience": "열정 학습자",
                "recommended": True,
            },
            {
                "id": "annual",
                "name": "연간 프리미엄",
                "price": 159000,
                "billing_cycle": "yearly",
                "original_price": 238800,  # 19900 * 12
                "discount_percent": 33,
                "features": [
                    {"name": "프리미엄 모든 기능", "included": True},
                    {"name": "1:1 질문 (월 10회)", "included": True},
                    {"name": "모의고사 해설 강의", "included": True},
                    {"name": "VIP 커뮤니티 접근", "included": True},
                ],
                "limits": {
                    "daily_problems": -1,
                    "hint_delay_minutes": 0,
                    "history_days": -1,
                    "questions_per_month": 10,
                },
                "target_audience": "수능 준비생",
            },
        ]

        self.pricing_plans = plans
        return plans

    def design_payment_system(self) -> Dict[str, Any]:
        """결제 시스템 설계"""
        self.log("결제 시스템 설계")

        payment_system = {
            "providers": [
                {
                    "name": "토스페이먼츠",
                    "priority": 1,
                    "methods": ["카드", "계좌이체", "가상계좌", "휴대폰"],
                    "fees": {"card": 2.5, "transfer": 1.0},
                },
                {
                    "name": "카카오페이",
                    "priority": 2,
                    "methods": ["카카오페이"],
                    "fees": {"kakao": 2.0},
                    "note": "카카오톡 연동으로 편의성 높음",
                },
            ],
            "subscription": {
                "type": "recurring",
                "retry_on_fail": True,
                "retry_count": 3,
                "grace_period_days": 7,
                "cancel_policy": {
                    "immediate": False,
                    "end_of_period": True,
                    "refund": "pro_rata",  # 일할 계산
                },
            },
            "billing": {
                "invoice_generation": "automatic",
                "payment_reminder": {
                    "days_before": [7, 3, 1],
                    "channel": "kakao",
                },
                "failed_payment": {
                    "notify": True,
                    "downgrade_after_days": 14,
                },
            },
            "promotions": {
                "first_month_discount": 50,  # 첫 달 50% 할인
                "referral_reward": 5000,  # 추천인 보상
                "student_discount": 20,  # 학생 할인
            },
        }

        return payment_system

    def create_marketing_strategy(self) -> Dict[str, Any]:
        """마케팅 전략 수립"""
        self.log("마케팅 전략 수립")

        strategy = {
            "target_segments": [
                {
                    "name": "고3 수험생",
                    "size": "약 50만명",
                    "pain_points": ["시간 부족", "자기주도 학습 어려움", "취약점 파악 어려움"],
                    "channels": ["카카오톡", "인스타그램", "학원 제휴"],
                },
                {
                    "name": "N수생",
                    "size": "약 15만명",
                    "pain_points": ["혼자 공부", "동기 부여", "체계적 관리"],
                    "channels": ["카카오톡", "네이버 카페", "유튜브"],
                },
                {
                    "name": "고1-2 예비 수험생",
                    "size": "약 100만명",
                    "pain_points": ["기초 부족", "학습 습관", "수능 적응"],
                    "channels": ["카카오톡", "틱톡", "학교 동아리"],
                },
            ],
            "campaigns": [
                {
                    "name": "수능 D-100 챌린지",
                    "type": "engagement",
                    "duration": "100일",
                    "content": "매일 한 문제 100일 연속 풀기",
                    "reward": "완주자 프리미엄 1개월 무료",
                    "expected_reach": 10000,
                },
                {
                    "name": "친구 추천 이벤트",
                    "type": "referral",
                    "reward_referrer": "프리미엄 1주 무료",
                    "reward_referee": "첫 달 50% 할인",
                    "expected_conversions": 500,
                },
                {
                    "name": "모의고사 시즌 프로모션",
                    "type": "seasonal",
                    "timing": ["6월 모의평가 전후", "9월 모의평가 전후"],
                    "offer": "해당 시험 기출 무료 제공",
                    "expected_signups": 2000,
                },
            ],
            "content_marketing": {
                "blog": {
                    "topics": ["수능 수학 공부법", "단원별 공략", "실수 줄이는 팁"],
                    "frequency": "주 2회",
                },
                "youtube": {
                    "content": ["1분 수학 팁", "킬러문항 해설", "멘탈 관리"],
                    "frequency": "주 1회",
                },
                "instagram": {
                    "content": ["오늘의 문제", "공부 동기부여", "사용자 후기"],
                    "frequency": "일 1회",
                },
            },
            "partnerships": [
                {"type": "학원 제휴", "benefit": "단체 할인 + 수익 분배"},
                {"type": "교육 인플루언서", "benefit": "콘텐츠 콜라보 + 코드 할인"},
                {"type": "교육청/학교", "benefit": "무료 제공 + 브랜드 인지도"},
            ],
        }

        return strategy

    def analyze_revenue(self, period: str = "monthly") -> Dict[str, Any]:
        """수익 분석"""
        self.log(f"수익 분석: {period}")

        # 시뮬레이션 데이터
        analysis = {
            "period": period,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_revenue": 15800000,
                "mrr": 12500000,  # Monthly Recurring Revenue
                "arr": 150000000,  # Annual Recurring Revenue
                "growth_rate": 15.5,  # %
            },
            "by_plan": {
                "free": {"users": 5000, "revenue": 0},
                "basic": {"users": 800, "revenue": 7920000},
                "premium": {"users": 350, "revenue": 6965000},
                "annual": {"users": 50, "revenue": 7950000},
            },
            "metrics": {
                "arpu": 12500,  # Average Revenue Per User
                "ltv": 150000,  # Lifetime Value
                "cac": 25000,  # Customer Acquisition Cost
                "ltv_cac_ratio": 6.0,
                "churn_rate": 5.2,  # %
                "conversion_rate": 8.5,  # free to paid %
            },
            "projections": {
                "next_month": 14375000,
                "quarter": 45000000,
                "year": 180000000,
            },
        }

        self.revenue_data[period] = analysis
        return analysis

    def analyze_users(self) -> Dict[str, Any]:
        """사용자 분석"""
        self.log("사용자 분석")

        analytics = {
            "generated_at": datetime.now().isoformat(),
            "total_users": 6200,
            "active_users": {
                "dau": 1500,  # Daily Active Users
                "wau": 3200,  # Weekly Active Users
                "mau": 4800,  # Monthly Active Users
            },
            "engagement": {
                "avg_session_duration": "12분 30초",
                "problems_solved_per_day": 2.3,
                "hint_usage_rate": 45.2,  # %
                "return_rate": 68.5,  # % 다음 날 재방문
            },
            "demographics": {
                "grade": {
                    "고1": 15,
                    "고2": 25,
                    "고3": 45,
                    "N수": 15,
                },
                "subscription": {
                    "free": 80.6,
                    "basic": 12.9,
                    "premium": 5.6,
                    "annual": 0.9,
                },
            },
            "behavior": {
                "peak_hours": ["07:00-08:00", "21:00-23:00"],
                "most_active_days": ["일요일", "토요일"],
                "avg_problems_before_upgrade": 15,
            },
            "satisfaction": {
                "nps_score": 42,  # Net Promoter Score
                "rating": 4.6,  # out of 5
                "reviews_count": 1250,
            },
        }

        self.user_analytics = analytics
        return analytics

    def create_business_report(self) -> Dict[str, Any]:
        """비즈니스 리포트 생성"""
        self.log("비즈니스 리포트 생성")

        revenue = self.analyze_revenue()
        users = self.analyze_users()

        report = {
            "report_date": datetime.now().isoformat(),
            "executive_summary": {
                "mrr": revenue["summary"]["mrr"],
                "total_users": users["total_users"],
                "paying_users": sum(
                    revenue["by_plan"][p]["users"]
                    for p in ["basic", "premium", "annual"]
                ),
                "growth_rate": revenue["summary"]["growth_rate"],
                "key_highlight": "프리미엄 구독자 전월 대비 20% 증가",
            },
            "revenue": revenue,
            "users": users,
            "key_metrics": {
                "ltv_cac_ratio": revenue["metrics"]["ltv_cac_ratio"],
                "churn_rate": revenue["metrics"]["churn_rate"],
                "nps_score": users["satisfaction"]["nps_score"],
            },
            "action_items": [
                {
                    "priority": "high",
                    "action": "연간 플랜 프로모션 강화",
                    "expected_impact": "MRR 10% 증가",
                },
                {
                    "priority": "medium",
                    "action": "무료→유료 전환율 개선",
                    "expected_impact": "전환율 2%p 상승",
                },
                {
                    "priority": "medium",
                    "action": "이탈 방지 캠페인",
                    "expected_impact": "이탈률 1%p 감소",
                },
            ],
        }

        return report

    def process_task(self, task: Task) -> Any:
        """작업 처리"""
        self.log(f"작업 처리: {task.title}")
        task.status = TaskStatus.IN_PROGRESS

        title_lower = task.title.lower()

        try:
            if "요금" in task.title or "pricing" in title_lower:
                result = self.design_pricing_plans()
                task.update_status(TaskStatus.COMPLETED, result=result)
                return result

            if "결제" in task.title or "payment" in title_lower:
                result = self.design_payment_system()
                task.update_status(TaskStatus.COMPLETED, result=result)
                return result

            if "마케팅" in task.title or "marketing" in title_lower:
                result = self.create_marketing_strategy()
                task.update_status(TaskStatus.COMPLETED, result=result)
                return result

            if "수익" in task.title or "revenue" in title_lower:
                result = self.analyze_revenue()
                task.update_status(TaskStatus.COMPLETED, result=result)
                return result

            if "사용자" in task.title or "user" in title_lower:
                result = self.analyze_users()
                task.update_status(TaskStatus.COMPLETED, result=result)
                return result

            if "보고서" in task.title or "report" in title_lower:
                result = self.create_business_report()
                task.update_status(TaskStatus.COMPLETED, result=result)
                return result

            # 기본 처리
            result = {"status": "processed", "task": task.title}
            task.update_status(TaskStatus.COMPLETED, result=result)
            return result

        except Exception as e:
            task.update_status(TaskStatus.FAILED, error=str(e))
            return {"error": str(e)}

    def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """메시지 처리"""
        self.log(f"메시지 처리: {message.message_type}")

        if message.message_type == "pricing_request":
            plans = self.design_pricing_plans()
            return self.send_message(
                message.sender,
                "pricing_response",
                {"plans": plans}
            )

        if message.message_type == "revenue_report_request":
            report = self.create_business_report()
            return self.send_message(
                message.sender,
                "revenue_report",
                report
            )

        if message.message_type == "user_analytics_request":
            analytics = self.analyze_users()
            return self.send_message(
                message.sender,
                "user_analytics",
                analytics
            )

        return None

    def get_pricing_plans(self) -> List[Dict]:
        """요금제 조회"""
        if not self.pricing_plans:
            self.design_pricing_plans()
        return self.pricing_plans
