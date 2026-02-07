"""
Dev 에이전트 - 개발 인프라 관리
서버 관리, 의존성 체크, 프로젝트 구조 분석, 코드 통계
"""

import os
import sys
import subprocess
import signal
from pathlib import Path
from typing import Optional, Any, Dict
from datetime import datetime

from .base import BaseAgent, Task, AgentMessage

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class DevAgent(BaseAgent):
    """
    개발 관리 에이전트

    역할:
    - FastAPI 서버 시작/종료/상태 확인
    - 의존성 체크 (requirements.txt vs 설치된 패키지)
    - 프로젝트 구조 분석
    - 코드 통계 (파일 수, 라인 수)
    """

    def __init__(self):
        super().__init__(
            name="dev",
            role="개발 관리",
            capabilities=[
                "서버 관리",
                "의존성 체크",
                "프로젝트 구조",
                "코드 통계",
            ]
        )
        self._server_process = None

    def check_server(self, port: int = 8000) -> Dict[str, Any]:
        """
        서버 상태 확인 (/health 엔드포인트)

        Args:
            port: 서버 포트

        Returns:
            서버 상태
        """
        self.log(f"서버 상태 확인 (port={port})")
        import urllib.request
        import urllib.error

        url = f"http://localhost:{port}/health"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                status_code = resp.status
                body = resp.read().decode("utf-8")
            return {
                "success": True,
                "running": True,
                "url": url,
                "status_code": status_code,
                "response": body,
            }
        except urllib.error.URLError:
            return {"success": True, "running": False, "url": url, "message": "서버 응답 없음"}
        except Exception as e:
            return {"success": True, "running": False, "url": url, "error": str(e)}

    def start_server(self, port: int = 8000) -> Dict[str, Any]:
        """
        FastAPI 서버 시작 (백그라운드)

        Args:
            port: 서버 포트

        Returns:
            시작 결과
        """
        self.log(f"서버 시작 (port={port})")

        # 이미 실행 중인지 확인
        status = self.check_server(port)
        if status.get("running"):
            return {"success": True, "message": "서버가 이미 실행 중입니다", "port": port}

        try:
            self._server_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "server.main:app",
                 "--host", "0.0.0.0", "--port", str(port)],
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            # 잠시 대기 후 확인
            import time
            time.sleep(2)

            if self._server_process.poll() is not None:
                stderr = self._server_process.stderr.read().decode("utf-8", errors="replace")
                return {"success": False, "error": f"서버 시작 실패: {stderr[:500]}"}

            return {
                "success": True,
                "message": "서버 시작됨",
                "port": port,
                "pid": self._server_process.pid,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop_server(self) -> Dict[str, Any]:
        """서버 종료"""
        self.log("서버 종료")

        if self._server_process and self._server_process.poll() is None:
            self._server_process.terminate()
            self._server_process.wait(timeout=5)
            self._server_process = None
            return {"success": True, "message": "서버 종료됨"}

        return {"success": True, "message": "실행 중인 서버 없음"}

    def check_dependencies(self) -> Dict[str, Any]:
        """
        requirements.txt와 실제 설치된 패키지 비교

        Returns:
            일치/누락/버전 불일치 정보
        """
        self.log("의존성 체크")

        req_file = PROJECT_ROOT / "requirements.txt"
        if not req_file.exists():
            return {"success": False, "error": "requirements.txt 없음"}

        # requirements.txt 파싱
        required = {}
        with open(req_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ">=" in line:
                    name, ver = line.split(">=", 1)
                    required[name.strip().lower()] = {"op": ">=", "version": ver.strip()}
                elif "==" in line:
                    name, ver = line.split("==", 1)
                    required[name.strip().lower()] = {"op": "==", "version": ver.strip()}
                else:
                    required[line.lower()] = {"op": None, "version": None}

        # pip로 설치된 패키지 조회
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=json"],
                capture_output=True, text=True, timeout=30,
            )
            installed_list = __import__("json").loads(result.stdout)
            installed = {pkg["name"].lower(): pkg["version"] for pkg in installed_list}
        except Exception as e:
            return {"success": False, "error": f"pip list 실패: {e}"}

        # 비교
        ok = []
        missing = []
        version_mismatch = []

        for name, req in required.items():
            if name in installed:
                ok.append({"name": name, "installed": installed[name], "required": req.get("version")})
            else:
                # pip은 하이픈/언더스코어를 치환하므로 재시도
                alt_name = name.replace("-", "_")
                alt_name2 = name.replace("_", "-")
                if alt_name in installed:
                    ok.append({"name": name, "installed": installed[alt_name]})
                elif alt_name2 in installed:
                    ok.append({"name": name, "installed": installed[alt_name2]})
                else:
                    missing.append(name)

        return {
            "success": True,
            "total_required": len(required),
            "installed": len(ok),
            "missing": missing,
            "missing_count": len(missing),
        }

    def get_project_structure(self) -> Dict[str, Any]:
        """
        프로젝트 디렉토리 구조 분석

        Returns:
            디렉토리별 파일 수, 주요 파일 목록
        """
        self.log("프로젝트 구조 분석")

        exclude_dirs = {"venv", "node_modules", "__pycache__", ".git", ".claude", "credentials"}
        structure = {}

        for root, dirs, files in os.walk(PROJECT_ROOT):
            # 제외 디렉토리 필터링
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            rel_path = Path(root).relative_to(PROJECT_ROOT)
            rel_str = str(rel_path) if str(rel_path) != "." else "(root)"

            # 확장자별 파일 분류
            py_files = [f for f in files if f.endswith(".py")]
            jsx_files = [f for f in files if f.endswith(".jsx")]
            html_files = [f for f in files if f.endswith(".html")]
            sql_files = [f for f in files if f.endswith(".sql")]
            other_important = [f for f in files if f.endswith((".md", ".txt", ".json", ".env"))]

            if py_files or jsx_files or html_files or sql_files:
                structure[rel_str] = {
                    "py": py_files,
                    "jsx": jsx_files,
                    "html": html_files,
                    "sql": sql_files,
                    "other": other_important,
                }

        return {
            "success": True,
            "directories": len(structure),
            "structure": structure,
        }

    def get_code_stats(self) -> Dict[str, Any]:
        """
        코드 통계: 파일 수, 라인 수, 모듈 수

        Returns:
            코드 통계
        """
        self.log("코드 통계 분석")

        exclude_dirs = {"venv", "node_modules", "__pycache__", ".git", ".claude"}
        stats = {"py": {"files": 0, "lines": 0}, "jsx": {"files": 0, "lines": 0}}

        for root, dirs, files in os.walk(PROJECT_ROOT):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for f in files:
                fpath = Path(root) / f
                ext = fpath.suffix

                if ext in (".py", ".jsx"):
                    key = "py" if ext == ".py" else "jsx"
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                            line_count = sum(1 for _ in fp)
                        stats[key]["files"] += 1
                        stats[key]["lines"] += line_count
                    except Exception:
                        pass

        # 에이전트 모듈 수
        agents_dir = PROJECT_ROOT / "agents"
        agent_modules = [f.stem for f in agents_dir.glob("*.py") if f.stem != "__init__"]

        # src 모듈 수
        src_dir = PROJECT_ROOT / "src"
        src_modules = [f.stem for f in src_dir.glob("*.py") if f.stem != "__init__"] if src_dir.exists() else []

        # server 모듈 수
        server_dir = PROJECT_ROOT / "server"
        server_modules = [f.stem for f in server_dir.glob("*.py") if f.stem != "__init__"] if server_dir.exists() else []

        return {
            "success": True,
            "python": stats["py"],
            "jsx": stats["jsx"],
            "total_files": stats["py"]["files"] + stats["jsx"]["files"],
            "total_lines": stats["py"]["lines"] + stats["jsx"]["lines"],
            "modules": {
                "agents": agent_modules,
                "src": src_modules,
                "server": server_modules,
            },
        }

    def process_task(self, task: Task) -> Any:
        """작업 처리"""
        title = task.title.lower()
        if "server" in title or "서버" in title:
            if "start" in title or "시작" in title:
                return self.start_server()
            elif "stop" in title or "종료" in title:
                return self.stop_server()
            return self.check_server()
        elif "dep" in title or "의존" in title:
            return self.check_dependencies()
        elif "struct" in title or "구조" in title:
            return self.get_project_structure()
        elif "stat" in title or "통계" in title:
            return self.get_code_stats()
        return {"error": f"알 수 없는 작업: {task.title}"}

    def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """메시지 처리"""
        if message.message_type == "task_assigned":
            self.log(f"작업 수신: {message.content.get('task', {}).get('title', 'unknown')}")
        return None
