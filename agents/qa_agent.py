"""
QA 에이전트 - 품질 보증
코드 구문 검사, import 검증, API 엔드포인트 테스트, 설정 검증
"""

import os
import sys
import py_compile
from pathlib import Path
from typing import Optional, Any, Dict, List
from datetime import datetime

from .base import BaseAgent, Task, AgentMessage

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class QAAgent(BaseAgent):
    """
    품질 보증 에이전트

    역할:
    - Python 모듈 import 검증
    - 코드 구문 검사 (py_compile)
    - 환경 설정 검증
    - FastAPI 엔드포인트 테스트
    - 종합 품질 리포트
    """

    def __init__(self):
        super().__init__(
            name="qa",
            role="품질 보증",
            capabilities=[
                "import 검증",
                "구문 검사",
                "설정 검증",
                "API 테스트",
                "종합 리포트",
            ]
        )

    def check_imports(self) -> Dict[str, Any]:
        """
        프로젝트 주요 모듈 import 검증

        Returns:
            성공/실패한 모듈 목록
        """
        self.log("import 검증 시작")

        modules_to_check = [
            # src 모듈
            ("src.config", "설정 모듈"),
            ("src.supabase_service", "Supabase 서비스"),
            ("src.notion_service", "Notion 서비스"),
            ("src.google_drive_service", "Google Drive 서비스"),
            ("src.pdf_converter", "PDF 변환기"),
            ("src.answer_parser", "정답 파서"),
            ("src.supabase_storage", "Supabase Storage"),
            ("src.page_splitter", "페이지 분리기"),
            ("src.image_processor", "이미지 프로세서"),
            # agents 모듈
            ("agents.base", "에이전트 베이스"),
            ("agents.commander", "Commander"),
            ("agents.pipeline_agent", "Pipeline 에이전트"),
            ("agents.content_agent", "Content 에이전트"),
            ("agents.ops_agent", "Ops 에이전트"),
            ("agents.dev_agent", "Dev 에이전트"),
            ("agents.qa_agent", "QA 에이전트"),
            # server 모듈
            ("server.main", "FastAPI 앱"),
            ("server.auth", "인증 모듈"),
            ("server.scheduler", "스케줄러"),
            # 외부 라이브러리
            ("fastapi", "FastAPI"),
            ("supabase", "Supabase Client"),
            ("notion_client", "Notion Client"),
            ("fitz", "PyMuPDF"),
            ("PIL", "Pillow"),
        ]

        # 프로젝트 루트를 path에 추가
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))

        passed = []
        failed = []

        for module_name, description in modules_to_check:
            try:
                __import__(module_name)
                passed.append({"module": module_name, "description": description})
            except Exception as e:
                failed.append({
                    "module": module_name,
                    "description": description,
                    "error": str(e)[:200],
                })

        self.log(f"import 검증 완료: {len(passed)} 성공, {len(failed)} 실패")

        return {
            "success": True,
            "total": len(modules_to_check),
            "passed": len(passed),
            "failed": len(failed),
            "failed_modules": failed if failed else None,
        }

    def check_syntax(self) -> Dict[str, Any]:
        """
        모든 .py 파일 구문 검사 (py_compile)

        Returns:
            구문 오류 목록
        """
        self.log("구문 검사 시작")

        exclude_dirs = {"venv", "node_modules", "__pycache__", ".git", ".claude"}
        errors = []
        checked = 0

        for root, dirs, files in os.walk(PROJECT_ROOT):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for f in files:
                if not f.endswith(".py"):
                    continue

                fpath = os.path.join(root, f)
                checked += 1

                try:
                    py_compile.compile(fpath, doraise=True)
                except py_compile.PyCompileError as e:
                    rel = os.path.relpath(fpath, PROJECT_ROOT)
                    errors.append({"file": rel, "error": str(e)[:300]})

        self.log(f"구문 검사 완료: {checked}개 파일, {len(errors)}개 오류")

        return {
            "success": True,
            "total_files": checked,
            "errors": len(errors),
            "error_details": errors if errors else None,
        }

    def validate_config(self) -> Dict[str, Any]:
        """
        환경 설정 검증 (src/config.py의 validate_config 래핑)

        Returns:
            설정 검증 결과
        """
        self.log("설정 검증 시작")

        try:
            from dotenv import load_dotenv
            load_dotenv()

            from src.config import (
                SUPABASE_URL, SUPABASE_KEY, NOTION_TOKEN,
                NOTION_DATABASE_ID, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
                GOOGLE_DRIVE_FOLDER_ID, DOWNLOAD_PATH, OUTPUT_PATH,
            )

            checks = {
                "SUPABASE_URL": bool(SUPABASE_URL),
                "SUPABASE_KEY": bool(SUPABASE_KEY),
                "NOTION_TOKEN": bool(NOTION_TOKEN),
                "NOTION_DATABASE_ID": bool(NOTION_DATABASE_ID),
                "GOOGLE_CLIENT_ID": bool(GOOGLE_CLIENT_ID),
                "GOOGLE_CLIENT_SECRET": bool(GOOGLE_CLIENT_SECRET),
                "GOOGLE_DRIVE_FOLDER_ID": bool(GOOGLE_DRIVE_FOLDER_ID),
            }

            path_checks = {
                "DOWNLOAD_PATH": DOWNLOAD_PATH.exists() if DOWNLOAD_PATH else False,
                "OUTPUT_PATH": OUTPUT_PATH.exists() if OUTPUT_PATH else False,
            }

            missing = [k for k, v in checks.items() if not v]
            missing_paths = [k for k, v in path_checks.items() if not v]

            return {
                "success": True,
                "env_vars": checks,
                "paths": path_checks,
                "missing_env": missing if missing else None,
                "missing_paths": missing_paths if missing_paths else None,
                "all_ok": not missing and not missing_paths,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def test_endpoints(self, port: int = 8000) -> Dict[str, Any]:
        """
        FastAPI 엔드포인트 테스트 (TestClient 또는 HTTP)

        Args:
            port: 서버 포트

        Returns:
            엔드포인트별 테스트 결과
        """
        self.log("API 엔드포인트 테스트 시작")

        # TestClient로 직접 테스트 (서버 실행 불필요)
        try:
            from fastapi.testclient import TestClient
            from server.main import app

            client = TestClient(app)
            endpoints = [
                ("GET", "/", "홈페이지"),
                ("GET", "/health", "헬스체크"),
            ]

            results = []
            for method, path, desc in endpoints:
                try:
                    if method == "GET":
                        resp = client.get(path)
                    else:
                        resp = client.post(path)

                    results.append({
                        "endpoint": f"{method} {path}",
                        "description": desc,
                        "status_code": resp.status_code,
                        "ok": 200 <= resp.status_code < 400,
                    })
                except Exception as e:
                    results.append({
                        "endpoint": f"{method} {path}",
                        "description": desc,
                        "error": str(e)[:200],
                        "ok": False,
                    })

            passed = sum(1 for r in results if r.get("ok"))

            return {
                "success": True,
                "method": "TestClient",
                "total": len(results),
                "passed": passed,
                "failed": len(results) - passed,
                "results": results,
            }
        except Exception as e:
            return {"success": False, "error": f"TestClient 초기화 실패: {e}"}

    def run_full_check(self) -> Dict[str, Any]:
        """
        종합 품질 검사 (모든 검사 순차 실행)

        Returns:
            종합 리포트
        """
        self.log("종합 품질 검사 시작")
        start = datetime.now()

        report = {}

        # 1. 구문 검사
        self.log("  [1/4] 구문 검사...")
        report["syntax"] = self.check_syntax()

        # 2. import 검증
        self.log("  [2/4] import 검증...")
        report["imports"] = self.check_imports()

        # 3. 설정 검증
        self.log("  [3/4] 설정 검증...")
        report["config"] = self.validate_config()

        # 4. API 테스트
        self.log("  [4/4] API 테스트...")
        report["endpoints"] = self.test_endpoints()

        elapsed = (datetime.now() - start).total_seconds()

        # 종합 점수
        checks = [
            report["syntax"]["errors"] == 0,
            report["imports"]["failed"] == 0,
            report["config"].get("all_ok", False),
            report["endpoints"].get("failed", 1) == 0,
        ]
        score = sum(checks)

        self.log(f"종합 검사 완료: {score}/4 통과 ({elapsed:.1f}초)")

        return {
            "success": True,
            "score": f"{score}/4",
            "elapsed_seconds": round(elapsed, 1),
            "details": report,
        }

    def process_task(self, task: Task) -> Any:
        """작업 처리"""
        title = task.title.lower()
        if "import" in title:
            return self.check_imports()
        elif "syntax" in title or "구문" in title:
            return self.check_syntax()
        elif "config" in title or "설정" in title:
            return self.validate_config()
        elif "endpoint" in title or "api" in title:
            return self.test_endpoints()
        elif "full" in title or "종합" in title:
            return self.run_full_check()
        return {"error": f"알 수 없는 작업: {task.title}"}

    def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """메시지 처리"""
        if message.message_type == "task_assigned":
            self.log(f"작업 수신: {message.content.get('task', {}).get('title', 'unknown')}")
        return None
