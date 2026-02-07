"""
KICE Math 통합 파이프라인
Google Drive에서 문제/정답 PDF를 가져와 한 번에 처리합니다.

사용법:
    python run_pipeline.py                          # 전체 파이프라인
    python run_pipeline.py --year 2026 --exam CSAT  # 특정 시험만
    python run_pipeline.py --answer-only            # 정답만 파싱+등록
    python run_pipeline.py --dry-run                # 실행 없이 미리보기
    python run_pipeline.py --no-move                # 처리 후 이동 안함
"""

import os
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

# src 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import (
    DOWNLOAD_PATH,
    OUTPUT_PATH,
    GDRIVE_PROBLEMS_FOLDER_ID,
    GDRIVE_ANSWERS_FOLDER_ID,
    GDRIVE_PROCESSED_FOLDER_ID,
    FILENAME_PATTERN,
)
from src.google_drive_service import GoogleDriveService
from src.pdf_converter import PDFConverter
from src.supabase_service import SupabaseService
from src.supabase_storage import SupabaseStorageService
from src.answer_parser import AnswerParser


class UnifiedPipeline:
    """Google Drive ↔ Supabase 통합 파이프라인"""

    def __init__(self):
        self.drive = None  # lazy init
        self.converter = PDFConverter(dpi=250)
        self.storage = SupabaseStorageService()
        self.db = SupabaseService()
        self.answer_parser = AnswerParser()
        self.downloads_dir = DOWNLOAD_PATH
        self.output_dir = OUTPUT_PATH

    def _init_drive(self):
        """Google Drive 서비스 초기화 (필요 시)"""
        if not self.drive:
            self.drive = GoogleDriveService()

    def _parse_filename(self, filename: str) -> dict:
        """파일명에서 메타데이터 추출: 2026_CSAT_PROBLEM.pdf → {year, exam, file_type}"""
        match = re.match(FILENAME_PATTERN, filename)
        if not match:
            return None
        return {
            "year": int(match.group(1)),
            "exam": match.group(2),
            "file_type": match.group(3).upper(),
        }

    def _matches_filter(self, filename: str, year: int = None, exam: str = None) -> bool:
        """파일명이 year/exam 필터와 일치하는지 확인"""
        meta = self._parse_filename(filename)
        if not meta:
            return False
        if year and meta["year"] != year:
            return False
        if exam and meta["exam"] != exam:
            return False
        return True

    # =========================================================================
    # Step 1: Google Drive 스캔
    # =========================================================================
    def step1_scan_drive(self, year=None, exam=None):
        """01_Problems, 02_Answers 폴더 스캔"""
        print("\n" + "=" * 60)
        print("  [Step 1] Google Drive 스캔")
        print("=" * 60)

        self._init_drive()

        problem_files = self.drive.list_pdf_files(GDRIVE_PROBLEMS_FOLDER_ID)
        answer_files = self.drive.list_pdf_files(GDRIVE_ANSWERS_FOLDER_ID)

        # 필터 적용
        if year or exam:
            problem_files = [f for f in problem_files if self._matches_filter(f["name"], year, exam)]
            answer_files = [f for f in answer_files if self._matches_filter(f["name"], year, exam)]

        print(f"  01_Problems: {len(problem_files)}개 PDF")
        for f in problem_files:
            size_kb = int(f.get("size", 0)) // 1024
            print(f"    - {f['name']} ({size_kb}KB)")

        print(f"  02_Answers:  {len(answer_files)}개 PDF")
        for f in answer_files:
            size_kb = int(f.get("size", 0)) // 1024
            print(f"    - {f['name']} ({size_kb}KB)")

        return problem_files, answer_files

    # =========================================================================
    # Step 2-5: 문제 PDF 처리
    # =========================================================================
    def step2_5_process_problems(self, problem_files: list):
        """문제 PDF: 다운로드 → 이미지 분리 → Storage 업로드 → DB 등록"""
        if not problem_files:
            print("\n  문제 PDF 없음 - 건너뜀")
            return []

        all_results = []

        for pf in problem_files:
            meta = self._parse_filename(pf["name"])
            if not meta:
                print(f"\n  파일명 형식 오류: {pf['name']} - 건너뜀")
                continue

            year, exam = meta["year"], meta["exam"]

            print("\n" + "=" * 60)
            print(f"  [Step 2] 문제 PDF 다운로드: {pf['name']}")
            print("=" * 60)

            # 다운로드
            pdf_path = self.drive.download_file(pf["id"], destination=self.downloads_dir)

            # PDF → 이미지
            print("\n  [Step 3] PDF → 이미지 변환")
            output_subdir = self.output_dir / f"{year}_{exam}"
            output_subdir.mkdir(parents=True, exist_ok=True)
            page_images = self.converter.pdf_to_images(pdf_path, output_folder=output_subdir)
            print(f"    {len(page_images)}페이지 변환 완료")

            # 하이브리드 분리 (Q1-Q22)
            print("\n  [Step 4] 하이브리드 분리 (Template + OCR)")
            from src.page_splitter import process_exam_pdf
            from PIL import Image

            # CSAT은 1-10페이지만 (공통과목)
            max_pages = min(len(page_images), 10) if exam == "CSAT" and year >= 2026 else len(page_images)
            pdf_pages = [Image.open(p) for p in page_images[:max_pages]]

            questions_dir = self.output_dir / f"{year}_{exam}_questions"
            split_summary = process_exam_pdf(
                pdf_pages=pdf_pages,
                exam=exam,
                year=year,
                output_dir=str(questions_dir),
                verify_ocr=False,  # OCR 없이 템플릿만 사용
            )
            print(f"    {split_summary['total_problems']}문제 분리 완료")

            if split_summary.get("needs_review"):
                print(f"    검토 필요: {split_summary['needs_review']}")

            # Storage 업로드
            print("\n  [Step 5] Supabase Storage 업로드")
            self.storage.create_bucket_if_not_exists()
            upload_results = self.storage.upload_problem_images(str(questions_dir))
            success_count = sum(1 for r in upload_results if r.get("success"))
            print(f"    {success_count}/{len(upload_results)} 이미지 업로드 완료")

            # DB 등록
            print("\n  [Step 5b] DB 문제 레코드 등록")
            url_map = {}
            for r in upload_results:
                if r.get("success"):
                    url_map[r.get("filename", "")] = r.get("url")

            saved = 0
            for result in split_summary.get("results", []):
                q_no = result["question_no"]
                problem_id = f"{year}_{exam}_Q{q_no:02d}"
                filename = f"{problem_id}.png"
                image_url = url_map.get(filename, "")

                problem_data = {
                    "problem_id": problem_id,
                    "year": year,
                    "exam": exam,
                    "question_no": q_no,
                    "problem_image_url": image_url,
                    "status": "ready",
                }

                try:
                    self.db.upsert_problem(problem_data)
                    saved += 1
                except Exception as e:
                    print(f"    DB 오류: {problem_id} - {e}")

            print(f"    {saved}개 문제 DB 등록 완료")

            all_results.append({
                "file": pf["name"],
                "file_id": pf["id"],
                "year": year,
                "exam": exam,
                "problems": split_summary["total_problems"],
                "uploaded": success_count,
                "saved": saved,
                "source_folder": GDRIVE_PROBLEMS_FOLDER_ID,
            })

        return all_results

    # =========================================================================
    # Step 6-7: 정답 PDF 처리
    # =========================================================================
    def step6_7_process_answers(self, answer_files: list, elective: str = "확률과통계"):
        """정답 PDF: 다운로드 → 파싱 → DB 업데이트"""
        if not answer_files:
            print("\n  정답 PDF 없음 - 건너뜀")
            return []

        all_results = []

        for af in answer_files:
            meta = self._parse_filename(af["name"])
            if not meta:
                print(f"\n  파일명 형식 오류: {af['name']} - 건너뜀")
                continue

            year, exam = meta["year"], meta["exam"]

            print("\n" + "=" * 60)
            print(f"  [Step 6] 정답 PDF 다운로드: {af['name']}")
            print("=" * 60)

            # 다운로드
            pdf_path = self.drive.download_file(af["id"], destination=self.downloads_dir)

            # 파싱
            print("\n  [Step 7] 정답 파싱 + DB 업데이트")
            parsed = self.answer_parser.parse_pdf(str(pdf_path))
            self.answer_parser.print_summary(parsed)

            # DB 레코드 생성
            records = self.answer_parser.to_db_records(parsed, year, exam, elective)
            print(f"\n  DB 업데이트: {len(records)}문제")

            updated = 0
            errors = 0
            for rec in records:
                pid = rec.pop("problem_id")
                try:
                    self.db.client.table("problems").update(rec).eq("problem_id", pid).execute()
                    updated += 1
                except Exception as e:
                    errors += 1
                    print(f"    오류: {pid} - {e}")

            print(f"    {updated}개 정답 업데이트 완료 (에러: {errors})")

            all_results.append({
                "file": af["name"],
                "file_id": af["id"],
                "year": year,
                "exam": exam,
                "answers_updated": updated,
                "errors": errors,
                "source_folder": GDRIVE_ANSWERS_FOLDER_ID,
            })

        return all_results

    # =========================================================================
    # Step 8: 처리 완료 파일 이동
    # =========================================================================
    def step8_move_processed(self, problem_results: list, answer_results: list):
        """처리 완료 파일을 04_Processed로 이동"""
        print("\n" + "=" * 60)
        print("  [Step 8] 처리 완료 파일 이동 → 04_Processed")
        print("=" * 60)

        all_files = problem_results + answer_results
        if not all_files:
            print("  이동할 파일 없음")
            return

        moved = 0
        for result in all_files:
            try:
                self.drive.move_file(
                    file_id=result["file_id"],
                    new_parent_id=GDRIVE_PROCESSED_FOLDER_ID,
                    old_parent_id=result.get("source_folder"),
                )
                print(f"  이동: {result['file']} → 04_Processed/")
                moved += 1
            except Exception as e:
                print(f"  이동 실패: {result['file']} - {e}")

        print(f"  {moved}개 파일 이동 완료")

    # =========================================================================
    # 전체 파이프라인 실행
    # =========================================================================
    def run(
        self,
        year: int = None,
        exam: str = None,
        answer_only: bool = False,
        dry_run: bool = False,
        no_move: bool = False,
        elective: str = "확률과통계",
    ):
        """통합 파이프라인 실행"""
        start_time = datetime.now()

        print("\n" + "=" * 60)
        print("    KICE Math 통합 파이프라인")
        print("=" * 60)
        print(f"  시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if year:
            print(f"  필터: year={year}")
        if exam:
            print(f"  필터: exam={exam}")
        if answer_only:
            print(f"  모드: 정답만 처리")
        if dry_run:
            print(f"  모드: DRY-RUN (실행 없음)")
        print(f"  선택과목: {elective}")

        # Step 1: Drive 스캔
        problem_files, answer_files = self.step1_scan_drive(year, exam)

        if dry_run:
            print("\n" + "=" * 60)
            print("  DRY-RUN 완료 - 실제 처리 없음")
            print("=" * 60)
            return

        # Step 2-5: 문제 처리
        problem_results = []
        if not answer_only:
            problem_results = self.step2_5_process_problems(problem_files)

        # Step 6-7: 정답 처리
        answer_results = self.step6_7_process_answers(answer_files, elective)

        # Step 8: 파일 이동
        if not no_move:
            self.step8_move_processed(problem_results, answer_results)

        # 요약
        elapsed = (datetime.now() - start_time).total_seconds()
        print("\n" + "=" * 60)
        print("    파이프라인 완료!")
        print("=" * 60)
        print(f"  소요 시간: {elapsed:.1f}초")

        if problem_results:
            total_problems = sum(r["problems"] for r in problem_results)
            total_uploaded = sum(r["uploaded"] for r in problem_results)
            print(f"  문제 처리: {total_problems}문제, {total_uploaded}이미지 업로드")

        if answer_results:
            total_answers = sum(r["answers_updated"] for r in answer_results)
            total_errors = sum(r["errors"] for r in answer_results)
            print(f"  정답 등록: {total_answers}문제 업데이트 (에러: {total_errors})")

        if not no_move:
            total_moved = len(problem_results) + len(answer_results)
            print(f"  파일 이동: {total_moved}개 → 04_Processed/")

        print(f"\n  Admin: http://localhost:8000/problem/admin")

    # =========================================================================
    # 로컬 PDF 직접 처리
    # =========================================================================
    def run_local(
        self,
        pdf_path: str,
        year: int,
        exam: str,
        elective: str = "확률과통계",
    ):
        """로컬 PDF 파일 직접 처리 (Google Drive 없이)"""
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            print(f"파일을 찾을 수 없습니다: {pdf_path}")
            return

        meta = self._parse_filename(pdf_path.name)
        if meta:
            year = meta.get("year", year)
            exam = meta.get("exam", exam)
            file_type = meta.get("file_type", "")
        else:
            file_type = "PROBLEM" if "PROBLEM" in pdf_path.name.upper() else "ANSWER"

        print(f"\n로컬 PDF 처리: {pdf_path.name}")
        print(f"  Year: {year}, Exam: {exam}, Type: {file_type}")

        if file_type == "ANSWER":
            # 정답 PDF 처리
            parsed = self.answer_parser.parse_pdf(str(pdf_path))
            self.answer_parser.print_summary(parsed)

            records = self.answer_parser.to_db_records(parsed, year, exam, elective)
            print(f"\n  DB 업데이트: {len(records)}문제")

            updated = 0
            for rec in records:
                pid = rec.pop("problem_id")
                try:
                    self.db.client.table("problems").update(rec).eq("problem_id", pid).execute()
                    updated += 1
                except Exception as e:
                    print(f"    오류: {pid} - {e}")

            print(f"  {updated}개 정답 업데이트 완료")
        else:
            # 문제 PDF 처리
            print("\n  PDF → 이미지 변환...")
            output_subdir = self.output_dir / f"{year}_{exam}"
            output_subdir.mkdir(parents=True, exist_ok=True)
            page_images = self.converter.pdf_to_images(pdf_path, output_folder=output_subdir)
            print(f"  {len(page_images)}페이지 변환")

            print("\n  하이브리드 분리...")
            from src.page_splitter import process_exam_pdf
            from PIL import Image

            max_pages = min(len(page_images), 10) if exam == "CSAT" and year >= 2026 else len(page_images)
            pdf_pages = [Image.open(p) for p in page_images[:max_pages]]

            questions_dir = self.output_dir / f"{year}_{exam}_questions"
            split_summary = process_exam_pdf(
                pdf_pages=pdf_pages,
                exam=exam,
                year=year,
                output_dir=str(questions_dir),
                verify_ocr=False,
            )
            print(f"  {split_summary['total_problems']}문제 분리")

            print("\n  Storage 업로드...")
            self.storage.create_bucket_if_not_exists()
            upload_results = self.storage.upload_problem_images(str(questions_dir))
            success = sum(1 for r in upload_results if r.get("success"))
            print(f"  {success}/{len(upload_results)} 업로드 완료")

            print("\n  DB 등록...")
            url_map = {r.get("filename", ""): r.get("url") for r in upload_results if r.get("success")}
            saved = 0
            for result in split_summary.get("results", []):
                q_no = result["question_no"]
                problem_id = f"{year}_{exam}_Q{q_no:02d}"
                problem_data = {
                    "problem_id": problem_id,
                    "year": year,
                    "exam": exam,
                    "question_no": q_no,
                    "problem_image_url": url_map.get(f"{problem_id}.png", ""),
                    "status": "ready",
                }
                try:
                    self.db.upsert_problem(problem_data)
                    saved += 1
                except Exception as e:
                    print(f"    오류: {problem_id} - {e}")
            print(f"  {saved}개 문제 DB 등록 완료")


def main():
    parser = argparse.ArgumentParser(
        description="KICE Math 통합 파이프라인",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python run_pipeline.py                          # Google Drive에서 전체 처리
  python run_pipeline.py --year 2026 --exam CSAT  # 2026 수능만
  python run_pipeline.py --answer-only            # 정답만 처리
  python run_pipeline.py --dry-run                # 미리보기
  python run_pipeline.py --local-pdf 2026_CSAT_ANSWER.pdf --year 2026  # 로컬 파일
        """,
    )
    parser.add_argument("--year", type=int, help="시험 년도 (예: 2026)")
    parser.add_argument("--exam", choices=["CSAT", "KICE6", "KICE9"], help="시험 유형")
    parser.add_argument("--answer-only", action="store_true", help="정답만 파싱+등록")
    parser.add_argument("--dry-run", action="store_true", help="실행 없이 미리보기")
    parser.add_argument("--no-move", action="store_true", help="처리 후 04_Processed로 이동 안함")
    parser.add_argument("--elective", default="확률과통계",
                        choices=["확률과통계", "미적분", "기하"], help="선택과목 (기본: 확률과통계)")
    parser.add_argument("--local-pdf", help="로컬 PDF 파일 경로 (Google Drive 대신)")

    args = parser.parse_args()

    pipeline = UnifiedPipeline()

    if args.local_pdf:
        pipeline.run_local(
            pdf_path=args.local_pdf,
            year=args.year or 2026,
            exam=args.exam or "CSAT",
            elective=args.elective,
        )
    else:
        pipeline.run(
            year=args.year,
            exam=args.exam,
            answer_only=args.answer_only,
            dry_run=args.dry_run,
            no_move=args.no_move,
            elective=args.elective,
        )


if __name__ == "__main__":
    main()
