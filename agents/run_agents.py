"""
에이전트 실행 스크립트
5개 에이전트 시스템 실행 및 프로젝트 관리
"""

import sys
import time
from datetime import datetime
from typing import Optional

from .base import TaskPriority
from .commander import CommanderAgent
from .designer import DesignerAgent
from .developer import DeveloperAgent
from .qa_optimizer import QAOptimizerAgent
from .business import BusinessAgent


class AgentOrchestrator:
    """에이전트 오케스트레이터 - 전체 시스템 관리"""

    def __init__(self):
        self.commander: Optional[CommanderAgent] = None
        self.agents = {}
        self.initialized = False

    def initialize(self):
        """시스템 초기화"""
        print("=" * 60)
        print("🚀 KICE 수학 카카오톡 발송 서비스 - 에이전트 시스템 시작")
        print("=" * 60)
        print()

        # 1. Commander 에이전트 생성
        print("📦 에이전트 초기화 중...")
        self.commander = CommanderAgent()
        print(f"   ✅ {self.commander.name} ({self.commander.role}) 생성됨")

        # 2. 전문 에이전트들 생성
        self.agents = {
            "designer": DesignerAgent(),
            "developer": DeveloperAgent(),
            "qa_optimizer": QAOptimizerAgent(),
            "business": BusinessAgent(),
        }

        # 3. Commander에 에이전트 등록
        for name, agent in self.agents.items():
            self.commander.register_agent(agent)
            print(f"   ✅ {agent.name} ({agent.role}) 등록됨")

        self.initialized = True
        print()
        print("✨ 모든 에이전트 초기화 완료!")
        print()

    def create_project_plan(self) -> dict:
        """프로젝트 계획 생성"""
        return {
            "name": "KICE 수학 카카오톡 발송 서비스",
            "description": "수능 수학 기출문제를 매일 카카오톡으로 발송하는 서비스",
            "created_at": datetime.now().isoformat(),
            "phases": [
                {
                    "name": "Phase 1: 기획 및 설계",
                    "description": "서비스 기획, 디자인, 비즈니스 모델 수립",
                    "priority": 1,
                    "tasks": [
                        {
                            "title": "요금제 설계",
                            "description": "무료/유료 요금제 구조 설계",
                            "assigned_to": "business",
                            "priority": 1,
                        },
                        {
                            "title": "카카오톡 템플릿 디자인",
                            "description": "메시지 템플릿 및 UI 설계",
                            "assigned_to": "designer",
                            "priority": 1,
                        },
                        {
                            "title": "마케팅 전략 수립",
                            "description": "타겟 고객 분석 및 마케팅 계획",
                            "assigned_to": "business",
                            "priority": 2,
                        },
                    ],
                },
                {
                    "name": "Phase 2: 개발",
                    "description": "백엔드/프론트엔드 개발",
                    "priority": 2,
                    "tasks": [
                        {
                            "title": "API 서버 개발",
                            "description": "카카오 API 연동 및 백엔드 개발",
                            "assigned_to": "developer",
                            "priority": 1,
                        },
                        {
                            "title": "웹 페이지 개발",
                            "description": "Next.js 기반 웹 인터페이스 개발",
                            "assigned_to": "developer",
                            "priority": 1,
                        },
                        {
                            "title": "결제 시스템 연동",
                            "description": "토스페이먼츠/카카오페이 연동",
                            "assigned_to": "developer",
                            "priority": 2,
                        },
                    ],
                },
                {
                    "name": "Phase 3: 품질 관리",
                    "description": "테스트 및 최적화",
                    "priority": 3,
                    "tasks": [
                        {
                            "title": "테스트 작성",
                            "description": "단위/통합/E2E 테스트 작성",
                            "assigned_to": "qa_optimizer",
                            "priority": 1,
                        },
                        {
                            "title": "성능 최적화",
                            "description": "응답 시간 및 성능 개선",
                            "assigned_to": "qa_optimizer",
                            "priority": 2,
                        },
                        {
                            "title": "모니터링 시스템 구축",
                            "description": "서비스 모니터링 및 알림 설정",
                            "assigned_to": "qa_optimizer",
                            "priority": 2,
                        },
                    ],
                },
                {
                    "name": "Phase 4: 런칭 준비",
                    "description": "최종 점검 및 런칭",
                    "priority": 4,
                    "tasks": [
                        {
                            "title": "사용자 분석 준비",
                            "description": "분석 대시보드 및 지표 설정",
                            "assigned_to": "business",
                            "priority": 2,
                        },
                        {
                            "title": "브랜딩 에셋 준비",
                            "description": "로고, 아이콘, 마케팅 이미지 제작",
                            "assigned_to": "designer",
                            "priority": 2,
                        },
                        {
                            "title": "최종 QA 점검",
                            "description": "런칭 전 전체 시스템 점검",
                            "assigned_to": "qa_optimizer",
                            "priority": 1,
                        },
                    ],
                },
            ],
        }

    def start_project(self):
        """프로젝트 시작"""
        if not self.initialized:
            self.initialize()

        print("📋 프로젝트 계획 생성 중...")
        project_plan = self.create_project_plan()
        print(f"   프로젝트: {project_plan['name']}")
        print(f"   총 {len(project_plan['phases'])}개 Phase")
        print()

        # Commander에게 프로젝트 시작 지시
        self.commander.start_project(project_plan)

    def run(self, max_iterations: int = 10):
        """에이전트 시스템 실행"""
        if not self.initialized:
            self.initialize()

        self.start_project()

        print()
        print("🔄 에이전트 실행 사이클 시작...")
        print()

        for i in range(max_iterations):
            print(f"--- Iteration {i + 1}/{max_iterations} ---")

            # 실행 사이클
            progress = self.commander.run_iteration()

            # 진행 상황 표시
            print(f"   진행률: {progress['progress_percent']}%")
            print(f"   완료: {progress['completed']}, 진행중: {progress['in_progress']}, 대기: {progress['pending']}")

            # 모든 작업 완료 확인
            if progress['pending'] == 0 and progress['in_progress'] == 0:
                print()
                print("✅ 모든 작업 완료!")
                break

            # 시뮬레이션을 위한 대기
            time.sleep(0.5)

        print()
        print(self.commander.generate_project_report())

    def execute_single_task(self, agent_name: str, task_type: str):
        """단일 작업 실행"""
        if not self.initialized:
            self.initialize()

        agent = self.agents.get(agent_name) or (
            self.commander if agent_name == "commander" else None
        )

        if not agent:
            print(f"❌ 에이전트를 찾을 수 없음: {agent_name}")
            return None

        print(f"🔧 {agent.name}에게 '{task_type}' 작업 실행...")

        # 작업 유형에 따른 실행
        if agent_name == "designer":
            if "템플릿" in task_type or "template" in task_type.lower():
                return agent.create_kakao_template("daily_problem")
            elif "레이아웃" in task_type:
                return agent.design_problem_image_layout()
            elif "ui" in task_type.lower():
                return agent.design_web_ui()
            elif "브랜딩" in task_type:
                return agent.create_branding_assets()

        elif agent_name == "developer":
            if "api" in task_type.lower():
                return agent.generate_api_routes()
            elif "페이지" in task_type or "page" in task_type.lower():
                return agent.generate_pages()
            elif "컴포넌트" in task_type or "component" in task_type.lower():
                return agent.generate_components()

        elif agent_name == "qa_optimizer":
            if "테스트" in task_type or "test" in task_type.lower():
                return agent.generate_test_suite()
            elif "모니터링" in task_type:
                return agent.setup_monitoring()
            elif "최적화" in task_type:
                return agent.optimize_performance()

        elif agent_name == "business":
            if "요금" in task_type or "pricing" in task_type.lower():
                return agent.design_pricing_plans()
            elif "결제" in task_type or "payment" in task_type.lower():
                return agent.design_payment_system()
            elif "마케팅" in task_type:
                return agent.create_marketing_strategy()
            elif "보고서" in task_type or "report" in task_type.lower():
                return agent.create_business_report()

        print(f"⚠️ 알 수 없는 작업 유형: {task_type}")
        return None

    def get_agent_capabilities(self):
        """모든 에이전트 역량 조회"""
        if not self.initialized:
            self.initialize()

        print()
        print("📚 에이전트 역량 목록")
        print("=" * 50)

        print(f"\n🎖️ {self.commander.name} ({self.commander.role})")
        for cap in self.commander.capabilities:
            print(f"   - {cap}")

        for name, agent in self.agents.items():
            print(f"\n👤 {agent.name} ({agent.role})")
            for cap in agent.capabilities:
                print(f"   - {cap}")

        print()

    def demo(self):
        """데모 실행 - 각 에이전트 주요 기능 시연"""
        if not self.initialized:
            self.initialize()

        print()
        print("🎬 에이전트 시스템 데모")
        print("=" * 60)

        # 1. Designer 데모
        print("\n--- Designer 에이전트 데모 ---")
        designer = self.agents["designer"]
        template = designer.create_kakao_template("daily_problem")
        print(f"   ✅ 카카오톡 템플릿 생성: {template['name']}")

        layout = designer.design_problem_image_layout()
        print(f"   ✅ 문제 이미지 레이아웃 설계: {layout['name']}")

        # 2. Developer 데모
        print("\n--- Developer 에이전트 데모 ---")
        developer = self.agents["developer"]
        pages = developer.generate_pages()
        print(f"   ✅ 페이지 생성: {len(pages)}개")

        api_routes = developer.generate_api_routes()
        print(f"   ✅ API 라우트 생성: {len(api_routes)}개")

        # 3. QA/Optimizer 데모
        print("\n--- QA/Optimizer 에이전트 데모 ---")
        qa = self.agents["qa_optimizer"]
        tests = qa.generate_test_suite()
        total_tests = sum(len(v) for v in tests.values() if isinstance(v, list))
        print(f"   ✅ 테스트 스위트 생성: {total_tests}개 테스트")

        monitoring = qa.setup_monitoring()
        print(f"   ✅ 모니터링 설정: {len(monitoring['metrics'])}개 메트릭")

        # 4. Business 데모
        print("\n--- Business 에이전트 데모 ---")
        business = self.agents["business"]
        plans = business.design_pricing_plans()
        print(f"   ✅ 요금제 설계: {len(plans)}개 플랜")

        strategy = business.create_marketing_strategy()
        print(f"   ✅ 마케팅 전략 수립: {len(strategy['campaigns'])}개 캠페인")

        print()
        print("=" * 60)
        print("✨ 데모 완료!")
        print()


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(
        description="KICE 수학 카카오톡 발송 서비스 - 에이전트 시스템"
    )
    parser.add_argument(
        "--mode",
        choices=["run", "demo", "capabilities", "task"],
        default="demo",
        help="실행 모드 선택",
    )
    parser.add_argument(
        "--agent",
        choices=["commander", "designer", "developer", "qa_optimizer", "business"],
        help="작업 실행할 에이전트 (task 모드에서 사용)",
    )
    parser.add_argument(
        "--task-type",
        help="실행할 작업 유형 (task 모드에서 사용)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="최대 실행 사이클 수 (run 모드에서 사용)",
    )

    args = parser.parse_args()

    orchestrator = AgentOrchestrator()

    if args.mode == "run":
        orchestrator.run(max_iterations=args.iterations)

    elif args.mode == "demo":
        orchestrator.demo()

    elif args.mode == "capabilities":
        orchestrator.get_agent_capabilities()

    elif args.mode == "task":
        if not args.agent or not args.task_type:
            print("❌ task 모드에서는 --agent와 --task-type이 필요합니다.")
            sys.exit(1)
        result = orchestrator.execute_single_task(args.agent, args.task_type)
        if result:
            import json
            print("\n📄 결과:")
            print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
