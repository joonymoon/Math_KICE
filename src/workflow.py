"""
자동화 워크플로우
Make.com을 대체하는 Python 기반 자동화 파이프라인

워크플로우:
1. Google Drive 폴더 감시
2. 새 PDF 파일 발견 시 다운로드
3. PDF → PNG 이미지 변환
4. 텍스트 추출 및 메타데이터 파싱
5. Supabase에 문제 데이터 저장
6. Notion에 검수 카드 생성
7. (선택) 이미지를 Google Drive에 업로드
"""

import time
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional

from .config import (
    DOWNLOAD_PATH,
    OUTPUT_PATH,
    GOOGLE_DRIVE_FOLDER_ID,
    GOOGLE_DRIVE_OUTPUT_FOLDER_ID,
    validate_config,
    print_config,
)
from .google_drive_service import GoogleDriveService
from .pdf_converter import PDFConverter, parse_filename
from .supabase_service import SupabaseService
from .notion_service import NotionService


class KICEWorkflow:
    """KICE 수학 문제 자동화 워크플로우"""

    def __init__(self):
        """서비스 초기화"""
        print("\n" + "=" * 60)
        print("KICE 수학 문제 관리 시스템 시작")
        print("=" * 60)

        # 설정 검증
        if not validate_config():
            raise ValueError("설정 오류로 시작할 수 없습니다.")

        print_config()

        # 서비스 초기화
        print("\n서비스 초기화 중...")
        self.drive = GoogleDriveService()
        self.converter = PDFConverter()
        self.supabase = SupabaseService()
        self.notion = NotionService()

        # 처리된 파일 ID 캐시
        self.processed_ids = set()

        print("\n모든 서비스 초기화 완료!")

    def load_processed_ids(self):
        """이미 처리된 파일 ID 로드"""
        self.processed_ids = self.supabase.get_processed_file_ids()
        print(f"이미 처리된 파일: {len(self.processed_ids)}개")

    def process_single_file(self, file_info: dict) -> Optional[dict]:
        """
        단일 파일 처리

        Args:
            file_info: Google Drive 파일 정보
                - id: 파일 ID
                - name: 파일명
                - webViewLink: 웹 링크

        Returns:
            처리 결과 딕셔너리
        """
        file_id = file_info["id"]
        file_name = file_info["name"]

        print(f"\n{'='*50}")
        print(f"파일 처리 시작: {file_name}")
        print(f"{'='*50}")

        try:
            # 1. 파일명에서 메타데이터 추출
            print("\n[1/6] 파일명 파싱...")
            metadata = parse_filename(file_name)
            print(f"  연도: {metadata.get('year')}")
            print(f"  시험: {metadata.get('exam')} ({metadata.get('exam_korean')})")
            print(f"  유형: {metadata.get('file_type')}")

            # 문제 ID 생성
            problem_id_base = f"{metadata.get('year')}_{metadata.get('exam')}"

            # 2. PDF 다운로드
            print("\n[2/6] PDF 다운로드...")
            pdf_path = self.drive.download_file(file_id, file_name)
            print(f"  저장 위치: {pdf_path}")

            # 3. PDF → PNG 변환
            print("\n[3/6] PDF → PNG 변환...")
            images = self.converter.pdf_to_images(pdf_path)
            print(f"  생성된 이미지: {len(images)}개")

            # 4. 텍스트 추출
            print("\n[4/6] 텍스트 추출...")
            extracted_text = self.converter.extract_text(pdf_path)
            problem_info = self.converter.extract_problem_info(extracted_text)
            print(f"  추출된 문항 번호: {problem_info.get('question_numbers', [])[:10]}...")
            print(f"  추출된 배점: {problem_info.get('scores', [])[:10]}...")

            # 5. 이미지 업로드 (선택적)
            image_folder_url = None
            if GOOGLE_DRIVE_OUTPUT_FOLDER_ID:
                print("\n[5/6] 이미지 업로드...")
                # 폴더 생성
                folder_name = f"{metadata.get('year')}_{metadata.get('exam')}_images"
                folder_id = self.drive.get_or_create_folder(
                    folder_name,
                    GOOGLE_DRIVE_OUTPUT_FOLDER_ID
                )

                # 이미지 업로드
                for image_path in images[:5]:  # 처음 5개만 테스트
                    self.drive.upload_file(image_path, folder_id)

                image_folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
                print(f"  이미지 폴더: {image_folder_url}")
            else:
                print("\n[5/6] 이미지 업로드 건너뜀 (출력 폴더 미설정)")

            # 6. 데이터 저장
            print("\n[6/6] 데이터 저장...")

            # 각 문제별로 저장 (정답표가 아닌 경우)
            if metadata.get('file_type', '').upper() != 'ANSWER':
                # 문제 PDF인 경우 - 대표 레코드 생성
                problem_data = {
                    "problem_id": problem_id_base,
                    "year": metadata.get("year"),
                    "exam": metadata.get("exam"),
                    "question_no": 0,  # 전체 PDF 대표
                    "extract_text": extracted_text[:5000],  # 텍스트 길이 제한
                    "source_ref": file_info.get("webViewLink"),
                    "page_images_folder": image_folder_url,
                    "status": "needs_review",
                }

                # Supabase 저장
                self.supabase.upsert_problem(problem_data)

                # Notion 카드 생성
                notion_data = {
                    "problem_id": problem_id_base,
                    "year": metadata.get("year"),
                    "exam": metadata.get("exam"),
                    "source_url": file_info.get("webViewLink"),
                    "image_folder_url": image_folder_url,
                    "extract_text": extracted_text[:2000],
                }
                self.notion.create_problem_card(notion_data)

            else:
                # 정답표 PDF인 경우 - 정답 업데이트
                print("  정답표 파일 감지 - 정답 업데이트")
                for q_no, answer in problem_info.get("answers", []):
                    problem_id = f"{problem_id_base}_Q{q_no}"
                    self.supabase.update_problem(problem_id, {
                        "answer": str(answer)
                    })

            # 처리 완료 표시
            self.processed_ids.add(file_id)

            print(f"\n파일 처리 완료: {file_name}")

            return {
                "file_id": file_id,
                "file_name": file_name,
                "problem_id": problem_id_base,
                "images_count": len(images),
                "status": "success",
            }

        except Exception as e:
            print(f"\n오류 발생: {e}")
            traceback.print_exc()
            return {
                "file_id": file_id,
                "file_name": file_name,
                "status": "error",
                "error": str(e),
            }

    def process_new_files(self, folder_id: Optional[str] = None) -> list:
        """
        새로운 파일 모두 처리

        Args:
            folder_id: 감시할 폴더 ID (기본값: 환경변수 설정)

        Returns:
            처리 결과 목록
        """
        folder_id = folder_id or GOOGLE_DRIVE_FOLDER_ID

        # 처리된 파일 ID 로드
        self.load_processed_ids()

        # 새 파일 조회
        new_files = self.drive.get_new_files(
            folder_id=folder_id,
            processed_ids=self.processed_ids
        )

        if not new_files:
            print("\n처리할 새 파일이 없습니다.")
            return []

        print(f"\n새로운 파일 {len(new_files)}개 발견!")

        results = []
        for i, file_info in enumerate(new_files, 1):
            print(f"\n[{i}/{len(new_files)}] 처리 중...")
            result = self.process_single_file(file_info)
            results.append(result)

        # 결과 요약
        success = sum(1 for r in results if r.get("status") == "success")
        errors = sum(1 for r in results if r.get("status") == "error")

        print(f"\n{'='*50}")
        print(f"처리 완료: 성공 {success}개, 실패 {errors}개")
        print(f"{'='*50}")

        return results

    def sync_notion_to_supabase(self):
        """Notion 검수 결과를 Supabase에 동기화"""
        print("\n" + "=" * 50)
        print("Notion → Supabase 동기화")
        print("=" * 50)

        synced = self.notion.sync_to_supabase(self.supabase)
        print(f"동기화 완료: {len(synced)}개")

        return synced

    def run_once(self):
        """한 번 실행"""
        print("\n" + "=" * 60)
        print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # 1. 새 파일 처리
        results = self.process_new_files()

        # 2. Notion 동기화
        self.sync_notion_to_supabase()

        # 3. 통계 출력
        self.supabase.print_stats()

        return results

    def run_scheduler(self, interval_minutes: int = 30):
        """
        스케줄러 실행 (주기적 실행)

        Args:
            interval_minutes: 실행 간격 (분)
        """
        print(f"\n스케줄러 시작: {interval_minutes}분 간격으로 실행")

        while True:
            try:
                self.run_once()
            except Exception as e:
                print(f"\n실행 중 오류: {e}")
                traceback.print_exc()

            print(f"\n다음 실행까지 {interval_minutes}분 대기...")
            time.sleep(interval_minutes * 60)


def process_single_pdf(pdf_path: str):
    """
    단일 PDF 파일 로컬 처리 (Google Drive 없이)

    Args:
        pdf_path: PDF 파일 경로
    """
    print(f"\n로컬 PDF 처리: {pdf_path}")

    converter = PDFConverter()
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        print(f"파일을 찾을 수 없습니다: {pdf_path}")
        return

    # 파일명 파싱
    metadata = parse_filename(pdf_path.name)
    print(f"메타데이터: {metadata}")

    # PDF → PNG 변환
    images = converter.pdf_to_images(pdf_path)
    print(f"생성된 이미지: {len(images)}개")

    # 텍스트 추출
    text = converter.extract_text(pdf_path)
    print(f"\n추출된 텍스트 (처음 500자):\n{text[:500]}...")

    # 문제 정보 추출
    info = converter.extract_problem_info(text)
    print(f"\n추출된 정보: {info}")

    return {
        "metadata": metadata,
        "images": images,
        "text": text,
        "info": info,
    }


# 메인 실행
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # 로컬 PDF 처리
        process_single_pdf(sys.argv[1])
    else:
        # 전체 워크플로우 실행
        workflow = KICEWorkflow()
        workflow.run_once()
