"""
KICE Math Problem Pipeline
Complete workflow: PDF -> Images -> Notion Review -> Supabase -> KakaoTalk

[1] PDF Collection (Google Drive)
      |
[2] Auto Processing (CloudConvert or PyMuPDF)
      |
[3] Hybrid Split (Template + OCR Verification)  <-- NEW!
      |
[4] Question Mapping (page -> question)
      |
[5] Review (Notion)
      |
[6] Database (Supabase)
      |
[7] Send (KakaoTalk)

Hybrid Split 워크플로우:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 1. 템플릿    │────►│ 2. OCR 검증 │────►│ 3. 수동 보정 │
│ 자동 분리    │     │ (문제번호   │     │ (오류 건만) │
│ (무료)      │     │  확인)      │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
     100%                95%                5%
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


class KICEPipeline:
    """Complete KICE math problem processing pipeline"""

    def __init__(self):
        self.downloads_dir = Path(os.getenv("DOWNLOAD_PATH", "./downloads"))
        self.output_dir = Path(os.getenv("OUTPUT_PATH", "./output"))
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def step1_download_pdf(self, folder_id: str = None) -> List[str]:
        """Step 1: Download PDFs from Google Drive"""
        from google_drive_service import GoogleDriveService

        print("\n" + "="*50)
        print("[STEP 1] Downloading PDFs from Google Drive")
        print("="*50)

        drive = GoogleDriveService()
        folder_id = folder_id or os.getenv("GOOGLE_DRIVE_FOLDER_ID")

        # List PDF files
        files = drive.list_files(folder_id)
        pdf_files = [f for f in files if f["name"].lower().endswith(".pdf")]

        if not pdf_files:
            print("No PDF files found in Google Drive folder")
            return []

        downloaded = []
        for pdf in pdf_files:
            local_path = self.downloads_dir / pdf["name"]
            drive.download_file(pdf["id"], str(local_path))
            downloaded.append(str(local_path))
            print(f"  Downloaded: {pdf['name']}")

        return downloaded

    def step2_convert_pdf(
        self,
        pdf_path: str,
        year: int,
        exam: str,
        use_cloudconvert: bool = False
    ) -> List[str]:
        """Step 2: Convert PDF to images"""
        print("\n" + "="*50)
        print("[STEP 2] Converting PDF to Images")
        print("="*50)

        output_subdir = self.output_dir / f"{year}_{exam}"
        output_subdir.mkdir(parents=True, exist_ok=True)

        if use_cloudconvert:
            try:
                from cloudconvert_service import CloudConvertService
                converter = CloudConvertService()
                results = converter.convert_pdf_per_page(
                    pdf_path=pdf_path,
                    output_dir=str(output_subdir),
                    prefix=f"{year}_{exam}_page_",
                    dpi=200
                )
                return [r["path"] for r in results]
            except Exception as e:
                print(f"CloudConvert failed: {e}")
                print("Falling back to PyMuPDF...")

        # Use PyMuPDF (local conversion)
        from pdf_converter import PDFConverter
        from pathlib import Path
        converter = PDFConverter(dpi=250)  # 250 DPI for high quality
        return converter.pdf_to_images(Path(pdf_path), output_folder=output_subdir)

    def step3_hybrid_split(
        self,
        year: int,
        exam: str,
        page_images_dir: str,
        verify_ocr: bool = True,
        page_range: tuple = None
    ) -> Dict:
        """
        Step 3: Hybrid Split - 템플릿 기반 분리 + OCR 검증

        한 페이지에 여러 문제가 있는 경우 자동으로 분리합니다.

        Args:
            year: 시험 년도
            exam: 시험 유형 (CSAT, KICE6, KICE9)
            page_images_dir: 페이지 이미지 디렉토리
            verify_ocr: OCR 검증 수행 여부
            page_range: 페이지 범위 (start, end) - 수학 공통만 처리 시 (1, 11)

        Returns:
            처리 결과 요약
        """
        print("\n" + "="*50)
        print("[STEP 3] Hybrid Split (Template + OCR)")
        print("="*50)

        from page_splitter import process_exam_pdf, HAS_TESSERACT
        from PIL import Image

        # 페이지 이미지 로드
        page_dir = Path(page_images_dir)
        image_files = sorted(page_dir.glob("*.png")) + sorted(page_dir.glob("*.jpg"))

        if not image_files:
            print(f"No images found in {page_images_dir}")
            return {"total_problems": 0, "needs_review": []}

        # ===== Edge Case 1: CSAT 템플릿 커버리지 경고 =====
        # CSAT 수학 템플릿은 1-11페이지(Q1-Q22)만 커버
        # 페이지 범위 지정 없이 11페이지 초과 시 경고
        if exam == "CSAT" and len(image_files) > 11 and not page_range:
            print("\n  ⚠️  WARNING: Template Coverage Limitation")
            print("  ───────────────────────────────────────")
            print(f"  Found {len(image_files)} pages, but CSAT template only covers pages 1-11")
            print("  Pages 1-11: Q1-Q22 (수학 공통) - Template supported")
            print("  Pages 12+: Q23-Q30 (선택 과목) - Manual review required")
            print("  Tip: Use --pages 1-11 to process only the common section")
            print("  ───────────────────────────────────────\n")

        # ===== Edge Case 2: 페이지 범위 유효성 검증 =====
        if page_range:
            start_page, end_page = page_range
            total_pages = len(image_files)

            # 범위 유효성 검사
            if start_page > end_page:
                print(f"  ❌ ERROR: Invalid page range - start ({start_page}) > end ({end_page})")
                return {"total_problems": 0, "needs_review": [], "error": "Invalid page range"}

            if start_page < 1:
                print(f"  ⚠️  WARNING: start_page ({start_page}) < 1, adjusted to 1")
                start_page = 1

            if end_page > total_pages:
                print(f"  ⚠️  WARNING: end_page ({end_page}) exceeds total pages ({total_pages})")
                print(f"     Adjusted to process pages {start_page}-{total_pages}")
                end_page = total_pages

            # BUG-001 FIX: 조정 후 역전 케이스 처리
            # 예: page_range=(15, 20) + total_pages=10 → start=15, end=10 역전
            if start_page > end_page:
                print(f"  ❌ ERROR: Page range {start_page}-{end_page} invalid after adjustment")
                print(f"     Requested start page ({start_page}) exceeds available pages ({total_pages})")
                return {"total_problems": 0, "needs_review": [], "error": "Page range out of bounds"}

            image_files = image_files[start_page - 1:end_page]  # 1-indexed to 0-indexed
            print(f"  Page range: {start_page}-{end_page} (Math Common)")

        pdf_pages = [Image.open(f) for f in image_files]
        print(f"  Found {len(pdf_pages)} page images")

        # ===== Edge Case 3: OCR 검증 불가 시 상세 경고 =====
        if verify_ocr and not HAS_TESSERACT:
            print("\n  ⚠️  WARNING: OCR Verification Unavailable")
            print("  ───────────────────────────────────────")
            print("  pytesseract not installed - OCR verification disabled")
            print("")
            print("  Impact on Accuracy:")
            print("  • Question number detection: Template-based only (may have 5-10% error)")
            print("  • Multi-problem pages: Relies on fixed ratios without verification")
            print("  • Recommendation: Review 'needs_review' items manually")
            print("")
            print("  To enable OCR verification:")
            print("  1. Install Tesseract: https://github.com/tesseract-ocr/tesseract")
            print("  2. pip install pytesseract")
            print("  ───────────────────────────────────────\n")
            verify_ocr = False

        # 출력 디렉토리
        output_dir = self.output_dir / f"{year}_{exam}_questions"

        # 하이브리드 분리 실행
        summary = process_exam_pdf(
            pdf_pages=pdf_pages,
            exam=exam,
            year=year,
            output_dir=str(output_dir),
            verify_ocr=verify_ocr
        )

        print(f"\n  Total problems: {summary['total_problems']}")
        print(f"  Needs review: {summary['needs_review_count']}")

        if summary['needs_review']:
            print(f"  Review list: {', '.join(summary['needs_review'][:5])}")
            if len(summary['needs_review']) > 5:
                print(f"    ... and {len(summary['needs_review']) - 5} more")

        return summary

    def step4_map_questions(
        self,
        year: int,
        exam: str,
        image_dir: str,
        interactive: bool = False
    ) -> Dict:
        """Step 4: Map pages to questions (Legacy - for manual mapping)"""
        print("\n" + "="*50)
        print("[STEP 4] Mapping Pages to Questions")
        print("="*50)

        from problem_mapper import ProblemMapper

        mapper = ProblemMapper()

        if interactive:
            from problem_mapper import interactive_mapping
            interactive_mapping(year, exam, image_dir)
            return mapper.load_mapping(year, exam)

        # Create default 1:1 mapping
        mapping = mapper.create_default_mapping(year, exam, image_dir)
        print(f"Created mapping for {mapping['total_questions']} questions")

        return mapping

    def step5_create_question_images(
        self,
        year: int,
        exam: str,
        source_dir: str
    ) -> List[Dict]:
        """Step 5: Create individual question images from mapped pages (Legacy)"""
        print("\n" + "="*50)
        print("[STEP 5] Creating Question Images (Legacy)")
        print("="*50)

        from problem_mapper import ProblemMapper

        mapper = ProblemMapper()
        output_dir = self.output_dir / f"{year}_{exam}_questions"

        results = mapper.create_question_images(
            year=year,
            exam=exam,
            source_dir=source_dir,
            output_dir=str(output_dir)
        )

        print(f"Created {len(results)} question images")
        return results

    def step6_upload_to_storage(self, image_dir: str) -> List[Dict]:
        """Step 6: Upload images to Supabase Storage"""
        print("\n" + "="*50)
        print("[STEP 6] Uploading to Supabase Storage")
        print("="*50)

        from supabase_storage import SupabaseStorageService

        storage = SupabaseStorageService()
        storage.create_bucket_if_not_exists()

        results = storage.upload_problem_images(image_dir)
        success = sum(1 for r in results if r["success"])
        failed = [r for r in results if not r["success"]]

        print(f"  Uploaded {success}/{len(results)} images")

        # ===== Edge Case 4: 업로드 실패 시 재시도 가이드 =====
        if failed:
            print(f"\n  ⚠️  WARNING: {len(failed)} uploads failed")
            print("  ───────────────────────────────────────")
            for f in failed[:3]:  # 처음 3개만 표시
                print(f"  • {f.get('file', 'unknown')}: {f.get('error', 'Unknown error')}")
            if len(failed) > 3:
                print(f"  • ... and {len(failed) - 3} more failures")
            print("")
            print("  Retry Options:")
            print(f"  1. Run again: python src/pipeline.py --upload-only --image-dir \"{image_dir}\"")
            print("  2. Check network connection and Supabase credentials")
            print("  3. Verify SUPABASE_URL and SUPABASE_KEY in .env")
            print("  ───────────────────────────────────────\n")

        return results

    def step7_create_notion_cards(
        self,
        year: int,
        exam: str,
        question_results: List[Dict]
    ) -> List[Dict]:
        """Step 7: Create Notion cards for review"""
        print("\n" + "="*50)
        print("[STEP 7] Creating Notion Cards for Review")
        print("="*50)

        from notion_service import NotionService

        notion = NotionService()
        created = []

        failed_cards = []

        for q in question_results:
            problem_data = {
                "problem_id": f"{year}_{exam}_Q{q['question_no']:02d}",
                "year": year,
                "exam": exam,
                "question_no": q["question_no"],
                "score": q.get("score", 3),
                "image_folder_url": q.get("output_image", "")
            }

            try:
                result = notion.create_problem_card(problem_data)
                created.append(result)
            except Exception as e:
                failed_cards.append({"question_no": q['question_no'], "error": str(e)})
                print(f"  Failed to create card for Q{q['question_no']}: {e}")

        print(f"  Created {len(created)} Notion cards")

        # ===== Edge Case 5: Notion 카드 생성 실패 시 가이드 =====
        if failed_cards:
            print(f"\n  ⚠️  WARNING: {len(failed_cards)} Notion cards failed")
            print("  ───────────────────────────────────────")
            print("  Common Causes:")
            print("  • Invalid NOTION_TOKEN - Check token in .env")
            print("  • Wrong DATABASE_ID - Verify database sharing permissions")
            print("  • API rate limit - Wait and retry")
            print("")
            print("  Retry Options:")
            print(f"  1. Run again: python src/pipeline.py --notion-only --year {year} --exam {exam}")
            print("  2. Verify Notion integration has database access")
            print("  ───────────────────────────────────────\n")

        return created

    def step8_save_to_database(
        self,
        year: int,
        exam: str,
        question_results: List[Dict],
        upload_results: List[Dict]
    ):
        """Step 8: Save problems to Supabase database"""
        print("\n" + "="*50)
        print("[STEP 8] Saving to Supabase Database")
        print("="*50)

        from supabase import create_client

        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )

        # Build URL mapping from upload results
        url_map = {}
        for r in upload_results:
            if r.get("success"):
                filename = r.get("filename", "")
                url_map[filename] = r.get("url")

        saved = 0
        for q in question_results:
            problem_id = f"{year}_{exam}_Q{q['question_no']:02d}"

            # Find corresponding URL
            filename = f"{problem_id}.png"
            image_url = url_map.get(filename, "")

            problem_data = {
                "problem_id": problem_id,
                "year": year,
                "exam": exam,
                "question_no": q["question_no"],
                "score": q.get("score", 3),
                "problem_image_url": image_url,
                "status": "needs_review"
            }

            try:
                supabase.table("problems").upsert(
                    problem_data,
                    on_conflict="problem_id"
                ).execute()
                saved += 1
                print(f"  Saved: {problem_id}")
            except Exception as e:
                print(f"  Failed: {problem_id} - {e}")

        print(f"\nSaved {saved} problems to database")

    def run_full_pipeline(
        self,
        pdf_path: str = None,
        year: int = 2026,
        exam: str = "CSAT",
        use_cloudconvert: bool = False,
        skip_notion: bool = False,
        interactive_mapping: bool = False,
        use_hybrid_split: bool = True,  # NEW: 하이브리드 분리 사용
        verify_ocr: bool = True,  # NEW: OCR 검증 수행
        page_range: tuple = None  # NEW: 페이지 범위 (수학 공통만 처리 시 (1, 11))
    ):
        """Run the complete pipeline"""
        print("\n" + "="*60)
        print("    KICE Math Problem Pipeline")
        print("="*60)

        # Step 1: Download (skip if pdf_path provided)
        if not pdf_path:
            downloaded = self.step1_download_pdf()
            if not downloaded:
                print("No PDFs to process")
                return
            pdf_path = downloaded[0]

        # Step 2: Convert PDF to images
        page_images = self.step2_convert_pdf(pdf_path, year, exam, use_cloudconvert)

        if not page_images:
            print("No images created")
            return

        source_dir = str(Path(page_images[0]).parent)
        questions_dir = self.output_dir / f"{year}_{exam}_questions"

        # Step 3: Hybrid Split OR Legacy Mapping
        if use_hybrid_split:
            # NEW: 하이브리드 분리 (템플릿 + OCR 검증)
            split_summary = self.step3_hybrid_split(
                year=year,
                exam=exam,
                page_images_dir=source_dir,
                verify_ocr=verify_ocr,
                page_range=page_range
            )

            # 분리 결과를 question_results 형식으로 변환
            question_results = [
                {
                    "question_no": r["question_no"],
                    "output_image": r["filepath"],
                    "score": 3,  # 기본 배점
                    "needs_review": r["needs_review"]
                }
                for r in split_summary.get("results", [])
            ]

            # 검토 필요한 문제가 있으면 경고
            if split_summary.get("needs_review"):
                print(f"\n[!] {len(split_summary['needs_review'])} problems need manual review!")
                print(f"   Check: {questions_dir}/split_summary.json")

        else:
            # Legacy: 기존 매핑 방식
            mapping = self.step4_map_questions(year, exam, source_dir, interactive_mapping)
            question_results = self.step5_create_question_images(year, exam, source_dir)

        if not question_results:
            print("No question images created")
            return

        # Step 6: Upload to storage
        upload_results = self.step6_upload_to_storage(str(questions_dir))

        # Step 7: Create Notion cards (optional)
        if not skip_notion:
            try:
                self.step7_create_notion_cards(year, exam, question_results)
            except Exception as e:
                print(f"Notion step skipped: {e}")

        # Step 8: Save to database
        self.step8_save_to_database(year, exam, question_results, upload_results)

        print("\n" + "="*60)
        print("    Pipeline Complete!")
        print("="*60)
        print(f"  - Questions processed: {len(question_results)}")
        print(f"  - Images uploaded: {sum(1 for r in upload_results if r.get('success'))}")

        if use_hybrid_split and split_summary.get("needs_review"):
            print(f"  - Needs review: {len(split_summary['needs_review'])}")

        print(f"\nNext steps:")
        print("  1. Review problems in Notion")
        if use_hybrid_split and split_summary.get("needs_review"):
            print("  2. Review flagged problems (check split_summary.json)")
            print("  3. Use Admin dashboard to send via KakaoTalk")
        else:
            print("  2. Use Admin dashboard to send via KakaoTalk")
        print(f"  URL: http://localhost:8000/problem/admin")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="KICE Math Problem Pipeline")
    parser.add_argument("--pdf", help="Path to PDF file")
    parser.add_argument("--year", type=int, default=2026, help="Exam year")
    parser.add_argument("--exam", default="CSAT", choices=["CSAT", "KICE6", "KICE9"])
    parser.add_argument("--cloudconvert", action="store_true", help="Use CloudConvert API")
    parser.add_argument("--skip-notion", action="store_true", help="Skip Notion integration")
    parser.add_argument("--interactive", action="store_true", help="Interactive mapping mode")
    parser.add_argument("--no-hybrid", action="store_true", help="Disable hybrid split (use legacy mapping)")
    parser.add_argument("--no-ocr", action="store_true", help="Skip OCR verification")
    parser.add_argument("--pages", help="Page range to process (e.g., '1-11' for math common only)")
    # Retry options (for failed operations)
    parser.add_argument("--upload-only", action="store_true", help="Only run upload step (retry failed uploads)")
    parser.add_argument("--notion-only", action="store_true", help="Only run Notion step (retry failed cards)")
    parser.add_argument("--image-dir", help="Image directory for --upload-only or --notion-only")

    args = parser.parse_args()

    # Parse page range if provided
    page_range = None
    if args.pages:
        try:
            parts = args.pages.split("-")
            if len(parts) == 2:
                page_range = (int(parts[0]), int(parts[1]))
            else:
                page_range = (int(parts[0]), int(parts[0]))  # Single page
        except ValueError:
            print(f"Invalid page range format: {args.pages}")
            print("Use format: '1-11' or single page '5'")
            return

    pipeline = KICEPipeline()

    # Handle retry-only modes
    if args.upload_only or args.notion_only:
        # Determine image directory
        if args.image_dir:
            image_dir = args.image_dir
        else:
            image_dir = str(pipeline.output_dir / f"{args.year}_{args.exam}_questions")

        if args.upload_only:
            print(f"\n[RETRY] Upload-only mode for: {image_dir}")
            results = pipeline.step6_upload_to_storage(image_dir)
            success = sum(1 for r in results if r.get("success"))
            print(f"\nUpload complete: {success}/{len(results)} succeeded")
            return

        if args.notion_only:
            print(f"\n[RETRY] Notion-only mode for: {image_dir}")
            # Load existing question results from split_summary.json
            import json
            summary_path = Path(image_dir) / "split_summary.json"
            if summary_path.exists():
                with open(summary_path) as f:
                    summary = json.load(f)
                question_results = [
                    {"question_no": r["question_no"], "output_image": r["filepath"], "score": 3}
                    for r in summary.get("results", [])
                ]
                pipeline.step7_create_notion_cards(args.year, args.exam, question_results)
            else:
                print(f"Error: {summary_path} not found")
                print("Run the full pipeline first or specify --image-dir")
            return

    # Run full pipeline
    pipeline.run_full_pipeline(
        pdf_path=args.pdf,
        year=args.year,
        exam=args.exam,
        use_cloudconvert=args.cloudconvert,
        skip_notion=args.skip_notion,
        interactive_mapping=args.interactive,
        use_hybrid_split=not args.no_hybrid,
        verify_ocr=not args.no_ocr,
        page_range=page_range
    )


if __name__ == "__main__":
    main()
