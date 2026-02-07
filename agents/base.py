"""
에이전트 기본 클래스 및 공통 데이터 구조
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any
import uuid
import json


class TaskStatus(Enum):
    """작업 상태"""
    PENDING = "pending"          # 대기 중
    IN_PROGRESS = "in_progress"  # 진행 중
    COMPLETED = "completed"      # 완료
    FAILED = "failed"            # 실패
    BLOCKED = "blocked"          # 차단됨 (의존성 대기)


class TaskPriority(Enum):
    """작업 우선순위"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    """작업 정의"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    assigned_to: str = ""  # 담당 에이전트
    created_by: str = ""   # 생성 에이전트
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[str] = field(default_factory=list)  # 의존 작업 ID
    subtasks: List["Task"] = field(default_factory=list)
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "assigned_to": self.assigned_to,
            "created_by": self.created_by,
            "status": self.status.value,
            "priority": self.priority.value,
            "dependencies": self.dependencies,
            "subtasks": [t.to_dict() for t in self.subtasks],
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    def update_status(self, status: TaskStatus, result: Any = None, error: str = None):
        self.status = status
        self.updated_at = datetime.now()
        if result is not None:
            self.result = result
        if error is not None:
            self.error = error


@dataclass
class AgentMessage:
    """에이전트 간 메시지"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    sender: str = ""      # 발신 에이전트
    receiver: str = ""    # 수신 에이전트 ("all" = 브로드캐스트)
    message_type: str = ""  # request, response, notification, report
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    reply_to: Optional[str] = None  # 응답인 경우 원본 메시지 ID

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "reply_to": self.reply_to,
        }


class BaseAgent(ABC):
    """에이전트 기본 클래스"""

    def __init__(self, name: str, role: str, capabilities: List[str]):
        self.name = name
        self.role = role
        self.capabilities = capabilities
        self.tasks: List[Task] = []
        self.message_queue: List[AgentMessage] = []
        self.status = "idle"  # idle, working, waiting
        self.logs: List[str] = []
        self._services_initialized = False

    def _init_services(self):
        """서비스 초기화 (각 에이전트에서 오버라이드)"""
        pass

    def ensure_services(self):
        """서비스가 초기화되었는지 확인하고, 안 되어 있으면 초기화"""
        if not self._services_initialized:
            self._init_services()
            self._services_initialized = True

    def safe_execute(self, func, *args, **kwargs) -> Dict[str, Any]:
        """안전한 서비스 호출 래퍼 (에러 로깅 포함)"""
        try:
            result = func(*args, **kwargs)
            return {"success": True, "data": result, "error": None}
        except Exception as e:
            error_msg = f"{func.__name__}() 실패: {e}"
            self.log(f"ERROR: {error_msg}")
            return {"success": False, "data": None, "error": error_msg}

    def log(self, message: str):
        """로그 기록"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{self.name}] {message}"
        self.logs.append(log_entry)
        print(log_entry)

    def receive_message(self, message: AgentMessage):
        """메시지 수신"""
        self.message_queue.append(message)
        self.log(f"메시지 수신: {message.message_type} from {message.sender}")

    def send_message(self, receiver: str, message_type: str, content: Dict[str, Any]) -> AgentMessage:
        """메시지 발신 (Commander를 통해 전달됨)"""
        message = AgentMessage(
            sender=self.name,
            receiver=receiver,
            message_type=message_type,
            content=content,
        )
        self.log(f"메시지 발신: {message_type} to {receiver}")
        return message

    def assign_task(self, task: Task):
        """작업 할당 받기"""
        task.assigned_to = self.name
        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = datetime.now()
        self.tasks.append(task)
        self.status = "working"
        self.log(f"작업 할당: {task.title}")

    def complete_task(self, task_id: str, result: Any = None):
        """작업 완료"""
        for task in self.tasks:
            if task.id == task_id:
                task.update_status(TaskStatus.COMPLETED, result=result)
                self.log(f"작업 완료: {task.title}")
                break

    def fail_task(self, task_id: str, error: str):
        """작업 실패"""
        for task in self.tasks:
            if task.id == task_id:
                task.update_status(TaskStatus.FAILED, error=error)
                self.log(f"작업 실패: {task.title} - {error}")
                break

    def get_pending_tasks(self) -> List[Task]:
        """대기 중인 작업 조회"""
        return [t for t in self.tasks if t.status == TaskStatus.PENDING]

    def get_active_tasks(self) -> List[Task]:
        """진행 중인 작업 조회"""
        return [t for t in self.tasks if t.status == TaskStatus.IN_PROGRESS]

    @abstractmethod
    def process_task(self, task: Task) -> Any:
        """작업 처리 (각 에이전트에서 구현)"""
        pass

    @abstractmethod
    def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """메시지 처리 (각 에이전트에서 구현)"""
        pass

    def get_status_report(self) -> Dict[str, Any]:
        """상태 보고서"""
        return {
            "agent": self.name,
            "role": self.role,
            "status": self.status,
            "capabilities": self.capabilities,
            "total_tasks": len(self.tasks),
            "pending_tasks": len(self.get_pending_tasks()),
            "active_tasks": len(self.get_active_tasks()),
            "completed_tasks": len([t for t in self.tasks if t.status == TaskStatus.COMPLETED]),
            "failed_tasks": len([t for t in self.tasks if t.status == TaskStatus.FAILED]),
        }

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name} status={self.status}>"
