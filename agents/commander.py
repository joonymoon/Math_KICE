"""
Commander 에이전트 - 총괄 지휘
작업 분배, 에이전트 조율, 진행 관리
"""

from typing import Optional, Dict, List, Any
from datetime import datetime
from .base import BaseAgent, Task, TaskStatus, TaskPriority, AgentMessage


class CommanderAgent(BaseAgent):
    """
    총괄 지휘 에이전트

    역할:
    - 전체 프로젝트 관리 및 조율
    - 작업 분배 및 우선순위 결정
    - 에이전트 간 커뮤니케이션 중재
    - 진행 상황 모니터링 및 보고
    """

    def __init__(self):
        super().__init__(
            name="commander",
            role="총괄 지휘",
            capabilities=[
                "프로젝트 관리",
                "작업 분배",
                "에이전트 조율",
                "진행 모니터링",
                "의사결정",
                "리소스 할당",
            ]
        )
        self.agents: Dict[str, BaseAgent] = {}
        self.project_tasks: List[Task] = []
        self.message_history: List[AgentMessage] = []
        self.project_status = "initialized"

    def register_agent(self, agent: BaseAgent):
        """에이전트 등록"""
        self.agents[agent.name] = agent
        self.log(f"에이전트 등록: {agent.name} ({agent.role})")

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """에이전트 조회"""
        return self.agents.get(name)

    def broadcast_message(self, message_type: str, content: Dict[str, Any]):
        """모든 에이전트에게 메시지 브로드캐스트"""
        message = AgentMessage(
            sender=self.name,
            receiver="all",
            message_type=message_type,
            content=content,
        )
        for agent in self.agents.values():
            agent.receive_message(message)
        self.message_history.append(message)
        self.log(f"브로드캐스트: {message_type}")

    def route_message(self, message: AgentMessage):
        """메시지 라우팅"""
        if message.receiver == "all":
            for agent in self.agents.values():
                if agent.name != message.sender:
                    agent.receive_message(message)
        elif message.receiver in self.agents:
            self.agents[message.receiver].receive_message(message)
        else:
            self.log(f"알 수 없는 수신자: {message.receiver}")

        self.message_history.append(message)

    def create_project_task(
        self,
        title: str,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        subtasks: List[Dict] = None,
    ) -> Task:
        """프로젝트 작업 생성"""
        task = Task(
            title=title,
            description=description,
            created_by=self.name,
            priority=priority,
        )

        if subtasks:
            for st in subtasks:
                subtask = Task(
                    title=st.get("title", ""),
                    description=st.get("description", ""),
                    assigned_to=st.get("assigned_to", ""),
                    created_by=self.name,
                    priority=TaskPriority(st.get("priority", 2)),
                )
                task.subtasks.append(subtask)

        self.project_tasks.append(task)
        self.log(f"프로젝트 작업 생성: {title}")
        return task

    def assign_task_to_agent(self, task: Task, agent_name: str) -> bool:
        """에이전트에게 작업 할당"""
        agent = self.get_agent(agent_name)
        if not agent:
            self.log(f"에이전트를 찾을 수 없음: {agent_name}")
            return False

        agent.assign_task(task)
        self.log(f"작업 할당: '{task.title}' → {agent_name}")

        # 할당 알림 메시지 전송
        self.route_message(AgentMessage(
            sender=self.name,
            receiver=agent_name,
            message_type="task_assigned",
            content={"task": task.to_dict()},
        ))

        return True

    def distribute_tasks(self, task: Task):
        """작업 자동 분배"""
        self.log(f"작업 분배 시작: {task.title}")

        # 하위 작업이 있으면 각각 할당
        if task.subtasks:
            for subtask in task.subtasks:
                if subtask.assigned_to:
                    self.assign_task_to_agent(subtask, subtask.assigned_to)
                else:
                    # 적합한 에이전트 자동 선택
                    agent = self._find_best_agent(subtask)
                    if agent:
                        self.assign_task_to_agent(subtask, agent.name)
        else:
            # 단일 작업
            agent = self._find_best_agent(task)
            if agent:
                self.assign_task_to_agent(task, agent.name)

    def _find_best_agent(self, task: Task) -> Optional[BaseAgent]:
        """작업에 적합한 에이전트 찾기"""
        # 키워드 기반 매칭
        task_text = f"{task.title} {task.description}".lower()

        agent_keywords = {
            "designer": ["디자인", "템플릿", "이미지", "ui", "ux", "레이아웃", "design"],
            "developer": ["개발", "api", "코드", "db", "서버", "기능", "develop", "code"],
            "qa_optimizer": ["테스트", "품질", "버그", "모니터링", "qa", "test", "bug"],
            "business": ["요금", "결제", "마케팅", "수익", "가격", "pricing", "marketing"],
        }

        for agent_name, keywords in agent_keywords.items():
            if any(kw in task_text for kw in keywords):
                agent = self.get_agent(agent_name)
                if agent:
                    return agent

        # 매칭 안 되면 가장 한가한 에이전트
        min_tasks = float('inf')
        best_agent = None
        for agent in self.agents.values():
            active = len(agent.get_active_tasks())
            if active < min_tasks:
                min_tasks = active
                best_agent = agent

        return best_agent

    def check_progress(self) -> Dict[str, Any]:
        """전체 진행 상황 확인"""
        total_tasks = len(self.project_tasks)
        completed = sum(1 for t in self.project_tasks if t.status == TaskStatus.COMPLETED)
        in_progress = sum(1 for t in self.project_tasks if t.status == TaskStatus.IN_PROGRESS)
        failed = sum(1 for t in self.project_tasks if t.status == TaskStatus.FAILED)
        pending = sum(1 for t in self.project_tasks if t.status == TaskStatus.PENDING)

        # 하위 작업 포함
        for task in self.project_tasks:
            for subtask in task.subtasks:
                total_tasks += 1
                if subtask.status == TaskStatus.COMPLETED:
                    completed += 1
                elif subtask.status == TaskStatus.IN_PROGRESS:
                    in_progress += 1
                elif subtask.status == TaskStatus.FAILED:
                    failed += 1
                else:
                    pending += 1

        progress = (completed / total_tasks * 100) if total_tasks > 0 else 0

        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "in_progress": in_progress,
            "failed": failed,
            "pending": pending,
            "progress_percent": round(progress, 1),
            "agents": {name: agent.get_status_report() for name, agent in self.agents.items()},
        }

    def generate_project_report(self) -> str:
        """프로젝트 보고서 생성"""
        progress = self.check_progress()

        report = []
        report.append("=" * 60)
        report.append("📊 KICE 수학 카카오톡 발송 서비스 - 프로젝트 현황")
        report.append("=" * 60)
        report.append(f"\n📈 전체 진행률: {progress['progress_percent']}%")
        report.append(f"   - 완료: {progress['completed']}개")
        report.append(f"   - 진행중: {progress['in_progress']}개")
        report.append(f"   - 대기중: {progress['pending']}개")
        report.append(f"   - 실패: {progress['failed']}개")

        report.append("\n👥 에이전트 현황:")
        for name, status in progress["agents"].items():
            emoji = {"idle": "😴", "working": "🔨", "waiting": "⏳"}.get(status["status"], "❓")
            report.append(f"   {emoji} {name} ({status['role']}): {status['status']}")
            report.append(f"      - 활성 작업: {status['active_tasks']}개")
            report.append(f"      - 완료 작업: {status['completed_tasks']}개")

        report.append("\n📋 프로젝트 작업:")
        for task in self.project_tasks:
            status_emoji = {
                TaskStatus.PENDING: "⏳",
                TaskStatus.IN_PROGRESS: "🔄",
                TaskStatus.COMPLETED: "✅",
                TaskStatus.FAILED: "❌",
            }.get(task.status, "❓")
            report.append(f"   {status_emoji} {task.title}")
            for subtask in task.subtasks:
                sub_emoji = {
                    TaskStatus.PENDING: "⏳",
                    TaskStatus.IN_PROGRESS: "🔄",
                    TaskStatus.COMPLETED: "✅",
                    TaskStatus.FAILED: "❌",
                }.get(subtask.status, "❓")
                report.append(f"      {sub_emoji} {subtask.title} [{subtask.assigned_to or '미할당'}]")

        report.append("=" * 60)

        return "\n".join(report)

    def process_task(self, task: Task) -> Any:
        """작업 처리"""
        self.log(f"작업 처리: {task.title}")

        if "분배" in task.title or "할당" in task.title:
            self.distribute_tasks(task)
            return {"status": "distributed"}

        if "보고" in task.title or "현황" in task.title:
            return self.generate_project_report()

        return {"status": "processed"}

    def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """메시지 처리"""
        self.log(f"메시지 처리: {message.message_type} from {message.sender}")

        if message.message_type == "task_completed":
            task_id = message.content.get("task_id")
            result = message.content.get("result")
            self.log(f"작업 완료 보고: {task_id}")
            # 다음 단계 작업 시작
            return self.send_message(
                message.sender,
                "acknowledgment",
                {"status": "received", "task_id": task_id}
            )

        if message.message_type == "help_request":
            # 다른 에이전트에게 도움 요청 전달
            target = message.content.get("target_agent")
            if target:
                self.route_message(AgentMessage(
                    sender=message.sender,
                    receiver=target,
                    message_type="assistance_needed",
                    content=message.content,
                ))
            return None

        if message.message_type == "status_report":
            # 상태 보고 수집
            return None

        return None

    def start_project(self, project_plan: Dict[str, Any]):
        """프로젝트 시작"""
        self.log("🚀 프로젝트 시작!")
        self.project_status = "in_progress"

        # 프로젝트 계획에서 작업 생성
        for phase in project_plan.get("phases", []):
            task = self.create_project_task(
                title=phase.get("name", ""),
                description=phase.get("description", ""),
                priority=TaskPriority(phase.get("priority", 2)),
                subtasks=phase.get("tasks", []),
            )
            self.distribute_tasks(task)

        # 시작 알림
        self.broadcast_message("project_started", {
            "project": project_plan.get("name", "KICE 카카오톡 발송 서비스"),
            "timestamp": datetime.now().isoformat(),
        })

    def run_iteration(self):
        """한 번의 실행 사이클"""
        # 1. 메시지 처리
        while self.message_queue:
            message = self.message_queue.pop(0)
            response = self.handle_message(message)
            if response:
                self.route_message(response)

        # 2. 각 에이전트 메시지 처리
        for agent in self.agents.values():
            while agent.message_queue:
                message = agent.message_queue.pop(0)
                response = agent.handle_message(message)
                if response:
                    self.route_message(response)

        # 3. 진행 상황 확인
        progress = self.check_progress()

        # 4. 블로킹된 작업 확인 및 해결
        self._check_blocked_tasks()

        return progress

    def _check_blocked_tasks(self):
        """블로킹된 작업 확인"""
        for task in self.project_tasks:
            if task.status == TaskStatus.BLOCKED:
                # 의존성 확인
                all_deps_done = all(
                    any(t.id == dep and t.status == TaskStatus.COMPLETED
                        for t in self.project_tasks)
                    for dep in task.dependencies
                )
                if all_deps_done:
                    task.status = TaskStatus.PENDING
                    self.distribute_tasks(task)
