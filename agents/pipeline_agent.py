"""
Pipeline 에이전트 - PDF 처리 파이프라인 실행
Google Drive → PDF 변환 → 이미지 분리 → Storage 업로드 → DB 등록
"""

import sys
import time
from pathlib import Path
from typing import Optional, Any, Dict, List
from datetime import datetime

from .base import BaseAgent, Task, TaskStatus, AgentMessage

# src 모듈 경로
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class PipelineAgent(BaseAgent):
    """
    PDF 처리 파이프라인 에이전트

    역할:
    - Google Drive에서 PDF 다운로드
    - PDF → 이미지 변환 및 문제별 분리
    - Supabase Storage 업로드
    - DB 문제 레코드 등록
    - 정답 PDF 파싱 및 업데이트
    """

    def __init__(self):
        super().__init__(
            name="pipeline",
            role="PDF 파이프라인",
            capabilities=[
                "PDF 다운로드",
                "이미지 변환",
                "문제 분리",
                "Storage 업로드",
                "DB 등록",
                "정답 파싱",
            ]
        )
        self._pipeline = None

    def _init_services(self):
        """UnifiedPipeline 초기화 (lazy)"""
        from dotenv import load_dotenv
        load_dotenv()
        from run_pipeline import UnifiedPipeline
        self._pipeline = UnifiedPipeline()
        self.log("파이프라인 서비스 초기화 완료")

    def run_full_pipeline(
        self,
        year: Optional[int] = None,
        exam: Optional[str] = None,
        dry_run: bool = False,
        no_move: bool = False,
        elective: str = "확률과통계",
    ) -> Dict[str, Any]:
        """
        전체 파이프라인 실행: Drive → PDF → Images → Upload → DB

        Args:
            year: 연도 필터
            exam: 시험 유형 필터 (CSAT, KICE6, KICE9)
            dry_run: True면 실행 없이 미리보기
            no_move: True면 처리 후 파일 이동 안함
            elective: 선택과목

        Returns:
            실행 결과 딕셔너리
        """
        self.ensure_services()
        self.status = "working"
        start_time = datetime.now()

        self.log(f"전체 파이프라인 시작 (year={year}, exam={exam}, dry_run={dry_run})")

        result = self.safe_execute(
            self._pipeline.run,
            year=year,
            exam=exam,
            dry_run=dry_run,
            no_move=no_move,
            elective=elective,
        )

        elapsed = (datetime.now() - start_time).total_seconds()
        self.status = "idle"

        if result["success"]:
            self.log(f"파이프라인 완료 ({elapsed:.1f}초)")
        else:
            self.log(f"파이프라인 실패: {result['error']}")

        return {
            "success": result["success"],
            "elapsed_seconds": round(elapsed, 1),
            "error": result["error"],
            "params": {"year": year, "exam": exam, "dry_run": dry_run},
        }

    def process_answers(
        self,
        year: Optional[int] = None,
        exam: Optional[str] = None,
        elective: str = "확률과통계",
    ) -> Dict[str, Any]:
        """
        정답 PDF만 처리: Drive 스캔 → 정답 파싱 → DB 업데이트

        Args:
            year: 연도 필터
            exam: 시험 유형 필터
            elective: 선택과목

        Returns:
            처리 결과
        """
        self.ensure_services()
        self.status = "working"
        self.log(f"정답 처리 시작 (year={year}, exam={exam})")

        result = self.safe_execute(
            self._pipeline.run,
            year=year,
            exam=exam,
            answer_only=True,
            elective=elective,
        )

        self.status = "idle"
        return {
            "success": result["success"],
            "error": result["error"],
            "params": {"year": year, "exam": exam, "answer_only": True},
        }

    def upload_local_pdf(
        self,
        pdf_path: str,
        year: int = 2026,
        exam: str = "CSAT",
        elective: str = "확률과통계",
    ) -> Dict[str, Any]:
        """
        로컬 PDF 파일 직접 처리 (Google Drive 없이)

        Args:
            pdf_path: PDF 파일 경로
            year: 연도
            exam: 시험 유형
            elective: 선택과목

        Returns:
            처리 결과
        """
        self.ensure_services()
        self.status = "working"
        self.log(f"로컬 PDF 처리: {pdf_path}")

        path = Path(pdf_path)
        if not path.exists():
            self.status = "idle"
            return {"success": False, "error": f"파일 없음: {pdf_path}"}

        result = self.safe_execute(
            self._pipeline.run_local,
            pdf_path=pdf_path,
            year=year,
            exam=exam,
            elective=elective,
        )

        self.status = "idle"
        return {
            "success": result["success"],
            "error": result["error"],
            "file": str(path.name),
        }

    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        파이프라인 현황 조회: DB의 문제 수, Drive 파일 수 등

        Returns:
            현황 딕셔너리
        """
        self.ensure_services()
        self.log("파이프라인 현황 조회")

        status = {"db_stats": None, "drive_files": None}

        # DB 통계
        db_result = self.safe_execute(self._pipeline.db.get_stats)
        if db_result["success"]:
            status["db_stats"] = db_result["data"]

        # Drive 파일 (선택적 - Drive 인증이 없을 수 있음)
        try:
            self._pipeline._init_drive()
            from src.config import GDRIVE_PROBLEMS_FOLDER_ID, GDRIVE_ANSWERS_FOLDER_ID
            problems = self._pipeline.drive.list_pdf_files(GDRIVE_PROBLEMS_FOLDER_ID)
            answers = self._pipeline.drive.list_pdf_files(GDRIVE_ANSWERS_FOLDER_ID)
            status["drive_files"] = {
                "problems": [f["name"] for f in problems],
                "answers": [f["name"] for f in answers],
            }
        except Exception as e:
            status["drive_files"] = {"error": str(e)}

        return status

    def process_task(self, task: Task) -> Any:
        """작업 처리"""
        title = task.title.lower()
        params = task.metadata

        if "pipeline" in title or "파이프라인" in title:
            return self.run_full_pipeline(
                year=params.get("year"),
                exam=params.get("exam"),
                dry_run=params.get("dry_run", False),
            )
        elif "answer" in title or "정답" in title:
            return self.process_answers(
                year=params.get("year"),
                exam=params.get("exam"),
            )
        elif "local" in title or "로컬" in title:
            return self.upload_local_pdf(
                pdf_path=params.get("pdf_path", ""),
                year=params.get("year", 2026),
                exam=params.get("exam", "CSAT"),
            )
        elif "status" in title or "현황" in title:
            return self.get_pipeline_status()

        return {"error": f"알 수 없는 작업: {task.title}"}

    def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """메시지 처리"""
        if message.message_type == "task_assigned":
            task_data = message.content.get("task", {})
            self.log(f"작업 수신: {task_data.get('title', 'unknown')}")
        return None
