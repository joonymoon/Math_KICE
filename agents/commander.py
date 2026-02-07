"""
Commander 에이전트 - 총괄 지휘
에이전트 조율, 상태 보고, 명령 디스패치
"""

from typing import Optional, Dict, List, Any
from datetime import datetime
from .base import BaseAgent, Task, AgentMessage


class CommanderAgent(BaseAgent):
    """
    총괄 지휘 에이전트

    역할:
    - 전체 에이전트 팀 관리 및 조율
    - CLI 명령을 적절한 에이전트로 디스패치
    - 전체 시스템 상태 보고서 생성
    - 에이전트 간 커뮤니케이션 중재
    """

    def __init__(self):
        super().__init__(
            name="commander",
            role="총괄 지휘",
            capabilities=[
                "에이전트 조율",
                "명령 디스패치",
                "상태 보고",
                "진행 모니터링",
            ]
        )
        self.agents: Dict[str, BaseAgent] = {}
        self.execution_history: List[Dict] = []

    def register_agent(self, agent: BaseAgent):
        """에이전트 등록"""
        self.agents[agent.name] = agent
        self.log(f"에이전트 등록: {agent.name} ({agent.role})")

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """에이전트 조회"""
        return self.agents.get(name)

    def execute_command(self, agent_name: str, command: str, **kwargs) -> Dict[str, Any]:
        """
        특정 에이전트의 명령 실행

        Args:
            agent_name: 에이전트 이름 (pipeline, content, ops)
            command: 실행할 명령
            **kwargs: 명령 파라미터

        Returns:
            실행 결과
        """
        agent = self.get_agent(agent_name)
        if not agent:
            return {"success": False, "error": f"에이전트 없음: {agent_name}"}

        self.log(f"명령 디스패치: {agent_name}.{command}({kwargs})")
        start_time = datetime.now()

        # 에이전트별 명령 매핑
        method = getattr(agent, command, None)
        if not method or not callable(method):
            return {"success": False, "error": f"명령 없음: {agent_name}.{command}"}

        try:
            result = method(**kwargs)
        except Exception as e:
            result = {"success": False, "error": str(e)}

        elapsed = (datetime.now() - start_time).total_seconds()

        # 실행 이력 기록
        self.execution_history.append({
            "agent": agent_name,
            "command": command,
            "params": kwargs,
            "elapsed": round(elapsed, 1),
            "success": result.get("success", True) if isinstance(result, dict) else True,
            "timestamp": datetime.now().isoformat(),
        })

        return result

    def get_full_status(self) -> Dict[str, Any]:
        """
        전체 시스템 상태 보고

        Returns:
            모든 에이전트의 상태 + 최근 실행 이력
        """
        agents_status = {}
        for name, agent in self.agents.items():
            agents_status[name] = {
                "role": agent.role,
                "status": agent.status,
                "capabilities": agent.capabilities,
                "total_tasks": len(agent.tasks),
                "logs_count": len(agent.logs),
            }

        return {
            "commander": {
                "status": self.status,
                "registered_agents": list(self.agents.keys()),
            },
            "agents": agents_status,
            "recent_executions": self.execution_history[-10:],
            "timestamp": datetime.now().isoformat(),
        }

    def generate_status_report(self) -> str:
        """포맷팅된 전체 상태 보고서"""
        status = self.get_full_status()

        lines = []
        lines.append("=" * 55)
        lines.append("  KICE Math Agent Team - 시스템 현황")
        lines.append("=" * 55)
        lines.append(f"  시각: {status['timestamp'][:19]}")
        lines.append(f"  등록된 에이전트: {len(status['agents'])}개")
        lines.append("")

        for name, info in status["agents"].items():
            status_icon = {"idle": "  ", "working": ">>", "waiting": ".."}.get(info["status"], "??")
            lines.append(f"  [{status_icon}] {name} ({info['role']})")
            lines.append(f"       상태: {info['status']}")
            lines.append(f"       기능: {', '.join(info['capabilities'][:3])}...")
            lines.append("")

        if status["recent_executions"]:
            lines.append("  [최근 실행]")
            for exec_item in status["recent_executions"][-5:]:
                ok = "OK" if exec_item.get("success") else "FAIL"
                lines.append(
                    f"    {exec_item['timestamp'][:19]} "
                    f"{exec_item['agent']}.{exec_item['command']} "
                    f"({exec_item['elapsed']}s) [{ok}]"
                )

        lines.append("=" * 55)
        return "\n".join(lines)

    def process_task(self, task: Task) -> Any:
        """작업 처리 - Commander는 다른 에이전트에게 위임"""
        title = task.title.lower()

        # 적합한 에이전트 찾기
        agent_name = self._find_best_agent(title)
        if agent_name:
            agent = self.get_agent(agent_name)
            if agent:
                return agent.process_task(task)

        return {"status": "no_suitable_agent", "task": task.title}

    def _find_best_agent(self, text: str) -> Optional[str]:
        """텍스트에서 적합한 에이전트 찾기"""
        keywords = {
            "pipeline": ["pdf", "pipeline", "파이프라인", "drive", "변환", "업로드", "정답"],
            "content": ["notion", "동기화", "sync", "검수", "검증", "validate", "콘텐츠"],
            "ops": ["통계", "stats", "health", "헬스", "보고", "report", "무결성", "integrity"],
            "dev": ["서버", "server", "의존성", "dep", "구조", "structure", "개발", "code-stats"],
            "qa": ["테스트", "test", "import", "syntax", "구문", "품질", "qa", "endpoint"],
        }

        text_lower = text.lower()
        for agent_name, kws in keywords.items():
            if any(kw in text_lower for kw in kws):
                return agent_name

        return None

    def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """메시지 처리"""
        self.log(f"메시지: {message.message_type} from {message.sender}")

        if message.message_type == "task_completed":
            self.log(f"작업 완료: {message.content.get('task_id')}")

        return None
