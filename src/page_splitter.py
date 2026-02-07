"""
KICE Math Page Splitter - Hybrid Automation Module
템플릿 기반 자동 분리 + OCR 검증 + 수동 보정 플래그

워크플로우:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 1. 템플릿    │────►│ 2. OCR 검증 │────►│ 3. 수동 보정 │
│ 자동 분리    │     │ (문제번호   │     │ (오류 건만) │
│ (무료)      │     │  확인)      │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
     100%                95%                5%

최종 업데이트: 2026-02-04
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from PIL import Image

# OCR은 선택적 의존성
try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    logging.warning("pytesseract not installed. OCR verification disabled.")

logger = logging.getLogger(__name__)


# ============================================
# 데이터 클래스
# ============================================

@dataclass
class CropRegion:
    """이미지 크롭 영역 (비율 기반)"""
    top: float      # 0.0 ~ 1.0
    bottom: float   # 0.0 ~ 1.0
    left: float = 0.0
    right: float = 1.0


@dataclass
class PageTemplate:
    """페이지별 문제 배치 템플릿"""
    page_num: int
    questions: List[int]  # 해당 페이지의 문제 번호들
    regions: List[CropRegion]  # 각 문제의 크롭 영역


@dataclass
class SplitResult:
    """분리 결과"""
    question_no: int
    image: Image.Image
    confidence: float = 1.0  # OCR 검증 신뢰도 (0.0 ~ 1.0)
    needs_review: bool = False  # 수동 검토 필요 여부
    review_reason: str = ""  # 검토 필요 사유


@dataclass
class ExamTemplate:
    """시험별 전체 템플릿"""
    exam_type: str  # CSAT, KICE6, KICE9
    year_range: Tuple[int, int]  # 적용 년도 범위
    pages: Dict[int, PageTemplate] = field(default_factory=dict)


# ============================================
# 수능 수학 템플릿 정의
# ============================================
# 수능 수학 시험지 구조 (2022~현재 기준):
# - 1~8페이지: 객관식 (한 페이지에 2~3문제)
# - 9~12페이지: 단답형 (한 페이지에 1~2문제)
# - 총 22문제 (객관식 15 + 단답형 7)

# 2026 CSAT uses two-column layout (different from 2022-2025)
CSAT_MATH_TEMPLATE_2026 = ExamTemplate(
    exam_type="CSAT",
    year_range=(2026, 2030),
    pages={
        # 페이지 1: 문제 1~4 (2x2 grid)
        1: PageTemplate(
            page_num=1,
            questions=[1, 2, 3, 4],
            regions=[
                CropRegion(top=0.12, bottom=0.52, left=0.0, right=0.50),   # Q1 left-top
                CropRegion(top=0.52, bottom=0.95, left=0.0, right=0.50),   # Q2 left-bottom
                CropRegion(top=0.12, bottom=0.52, left=0.50, right=1.0),   # Q3 right-top
                CropRegion(top=0.52, bottom=0.95, left=0.50, right=1.0),   # Q4 right-bottom
            ]
        ),
        # 페이지 2: 문제 5~7 (left: Q5,Q6 / right: Q7)
        2: PageTemplate(
            page_num=2,
            questions=[5, 6, 7],
            regions=[
                CropRegion(top=0.02, bottom=0.42, left=0.0, right=0.50),   # Q5 left-top
                CropRegion(top=0.42, bottom=0.90, left=0.0, right=0.50),   # Q6 left-bottom
                CropRegion(top=0.02, bottom=0.90, left=0.50, right=1.0),   # Q7 right-full
            ]
        ),
        # 페이지 3-11: Continue pattern (estimate, needs verification)
        3: PageTemplate(
            page_num=3,
            questions=[8, 9],
            regions=[
                CropRegion(top=0.05, bottom=0.90, left=0.0, right=0.50),   # Q8 left-full
                CropRegion(top=0.05, bottom=0.90, left=0.50, right=1.0),   # Q9 right-full
            ]
        ),
        4: PageTemplate(
            page_num=4,
            questions=[10, 11],
            regions=[
                CropRegion(top=0.05, bottom=0.90, left=0.0, right=0.50),   # Q10
                CropRegion(top=0.05, bottom=0.90, left=0.50, right=1.0),   # Q11
            ]
        ),
        5: PageTemplate(
            page_num=5,
            questions=[12, 13],
            regions=[
                CropRegion(top=0.05, bottom=0.90, left=0.0, right=0.50),   # Q12
                CropRegion(top=0.05, bottom=0.90, left=0.50, right=1.0),   # Q13
            ]
        ),
        6: PageTemplate(
            page_num=6,
            questions=[14, 15],
            regions=[
                CropRegion(top=0.05, bottom=0.90, left=0.0, right=0.50),   # Q14
                CropRegion(top=0.05, bottom=0.90, left=0.50, right=1.0),   # Q15
            ]
        ),
        7: PageTemplate(
            page_num=7,
            questions=[16, 17],
            regions=[
                CropRegion(top=0.05, bottom=0.90, left=0.0, right=0.50),   # Q16
                CropRegion(top=0.05, bottom=0.90, left=0.50, right=1.0),   # Q17
            ]
        ),
        8: PageTemplate(
            page_num=8,
            questions=[18, 19],
            regions=[
                CropRegion(top=0.05, bottom=0.90, left=0.0, right=0.50),   # Q18
                CropRegion(top=0.05, bottom=0.90, left=0.50, right=1.0),   # Q19
            ]
        ),
        9: PageTemplate(
            page_num=9,
            questions=[20, 21],
            regions=[
                CropRegion(top=0.05, bottom=0.90, left=0.0, right=0.50),   # Q20
                CropRegion(top=0.05, bottom=0.90, left=0.50, right=1.0),   # Q21
            ]
        ),
        10: PageTemplate(
            page_num=10,
            questions=[22],
            regions=[
                CropRegion(top=0.05, bottom=0.90, left=0.0, right=1.0),    # Q22 full-width
            ]
        ),
        # Page 11 is not used (template only goes to Q22)
    }
)

# Legacy template for 2022-2025 (vertical layout)
CSAT_MATH_TEMPLATE_LEGACY = ExamTemplate(
    exam_type="CSAT",
    year_range=(2022, 2025),
    pages={
        # 페이지 1: 문제 1~2
        1: PageTemplate(
            page_num=1,
            questions=[1, 2],
            regions=[
                CropRegion(top=0.10, bottom=0.52),  # Q1
                CropRegion(top=0.52, bottom=0.95),  # Q2
            ]
        ),
        # 페이지 2: 문제 3~5
        2: PageTemplate(
            page_num=2,
            questions=[3, 4, 5],
            regions=[
                CropRegion(top=0.05, bottom=0.35),  # Q3
                CropRegion(top=0.35, bottom=0.65),  # Q4
                CropRegion(top=0.65, bottom=0.95),  # Q5
            ]
        ),
        # 페이지 3: 문제 6~8
        3: PageTemplate(
            page_num=3,
            questions=[6, 7, 8],
            regions=[
                CropRegion(top=0.05, bottom=0.35),  # Q6
                CropRegion(top=0.35, bottom=0.65),  # Q7
                CropRegion(top=0.65, bottom=0.95),  # Q8
            ]
        ),
        # 페이지 4: 문제 9~10
        4: PageTemplate(
            page_num=4,
            questions=[9, 10],
            regions=[
                CropRegion(top=0.05, bottom=0.50),  # Q9
                CropRegion(top=0.50, bottom=0.95),  # Q10
            ]
        ),
        # 페이지 5: 문제 11~12
        5: PageTemplate(
            page_num=5,
            questions=[11, 12],
            regions=[
                CropRegion(top=0.05, bottom=0.50),  # Q11
                CropRegion(top=0.50, bottom=0.95),  # Q12
            ]
        ),
        # 페이지 6: 문제 13~14
        6: PageTemplate(
            page_num=6,
            questions=[13, 14],
            regions=[
                CropRegion(top=0.05, bottom=0.50),  # Q13
                CropRegion(top=0.50, bottom=0.95),  # Q14
            ]
        ),
        # 페이지 7: 문제 15 (마지막 객관식)
        7: PageTemplate(
            page_num=7,
            questions=[15],
            regions=[
                CropRegion(top=0.05, bottom=0.95),  # Q15
            ]
        ),
        # 페이지 8: 문제 16~17 (단답형 시작)
        8: PageTemplate(
            page_num=8,
            questions=[16, 17],
            regions=[
                CropRegion(top=0.05, bottom=0.50),  # Q16
                CropRegion(top=0.50, bottom=0.95),  # Q17
            ]
        ),
        # 페이지 9: 문제 18~19
        9: PageTemplate(
            page_num=9,
            questions=[18, 19],
            regions=[
                CropRegion(top=0.05, bottom=0.50),  # Q18
                CropRegion(top=0.50, bottom=0.95),  # Q19
            ]
        ),
        # 페이지 10: 문제 20~21
        10: PageTemplate(
            page_num=10,
            questions=[20, 21],
            regions=[
                CropRegion(top=0.05, bottom=0.50),  # Q20
                CropRegion(top=0.50, bottom=0.95),  # Q21
            ]
        ),
        # 페이지 11: 문제 22 (마지막 문제)
        11: PageTemplate(
            page_num=11,
            questions=[22],
            regions=[
                CropRegion(top=0.05, bottom=0.95),  # Q22
            ]
        ),
    }
)

# Use 2026 template by default
CSAT_MATH_TEMPLATE = CSAT_MATH_TEMPLATE_2026

# 6월/9월 모의평가 템플릿 (수능과 동일한 구조)
KICE6_TEMPLATE = ExamTemplate(
    exam_type="KICE6",
    year_range=(2022, 2030),
    pages=CSAT_MATH_TEMPLATE.pages  # 수능과 동일
)

KICE9_TEMPLATE = ExamTemplate(
    exam_type="KICE9",
    year_range=(2022, 2030),
    pages=CSAT_MATH_TEMPLATE.pages  # 수능과 동일
)

# 템플릿 레지스트리
TEMPLATES: Dict[str, ExamTemplate] = {
    "CSAT": CSAT_MATH_TEMPLATE,  # Default to 2026+ format
    "CSAT_2026": CSAT_MATH_TEMPLATE_2026,
    "CSAT_LEGACY": CSAT_MATH_TEMPLATE_LEGACY,
    "KICE6": KICE6_TEMPLATE,
    "KICE9": KICE9_TEMPLATE,
}


# ============================================
# 핵심 함수
# ============================================

def get_template(exam: str, year: int = None) -> Optional[ExamTemplate]:
    """시험 유형에 맞는 템플릿 반환"""
    # For CSAT, choose template based on year
    if exam == "CSAT" and year:
        if year >= 2026:
            template = CSAT_MATH_TEMPLATE_2026
        else:
            template = CSAT_MATH_TEMPLATE_LEGACY
    else:
        template = TEMPLATES.get(exam)

    if template and year:
        # 년도 범위 확인
        if not (template.year_range[0] <= year <= template.year_range[1]):
            logger.warning(f"Year {year} outside template range {template.year_range}")
    return template


def crop_by_region(image: Image.Image, region: CropRegion) -> Image.Image:
    """비율 기반으로 이미지 크롭"""
    width, height = image.size

    left = int(width * region.left)
    right = int(width * region.right)
    top = int(height * region.top)
    bottom = int(height * region.bottom)

    return image.crop((left, top, right, bottom))


def extract_question_number_ocr(image: Image.Image) -> Optional[int]:
    """OCR로 문제 번호 추출 (이미지 상단 영역에서)"""
    if not HAS_TESSERACT:
        return None

    try:
        # 상단 15% 영역만 크롭 (문제 번호가 있는 부분)
        width, height = image.size
        header_crop = image.crop((0, 0, width, int(height * 0.15)))

        # OCR 수행 (한글 + 숫자)
        text = pytesseract.image_to_string(
            header_crop,
            lang='kor+eng',
            config='--psm 6'  # 단일 블록으로 처리
        )

        # 문제 번호 패턴 찾기: "1.", "2.", ... "22." 또는 "1 .", "2 ." 등
        patterns = [
            r'^(\d{1,2})\s*\.',           # "1." or "22."
            r'^\s*(\d{1,2})\s+[^\d]',     # "1 [문제내용]"
            r'문제\s*(\d{1,2})',           # "문제 1"
        ]

        for pattern in patterns:
            match = re.search(pattern, text.strip(), re.MULTILINE)
            if match:
                return int(match.group(1))

        return None

    except Exception as e:
        logger.warning(f"OCR failed: {e}")
        return None


def template_split(
    page_image: Image.Image,
    page_template: PageTemplate
) -> List[Tuple[int, Image.Image]]:
    """템플릿 기반으로 페이지 분리"""
    results = []

    for question_no, region in zip(page_template.questions, page_template.regions):
        cropped = crop_by_region(page_image, region)
        results.append((question_no, cropped))

    return results


def hybrid_split(
    page_image: Image.Image,
    page_num: int,
    exam: str,
    year: int,
    verify_ocr: bool = True
) -> List[SplitResult]:
    """
    하이브리드 분리: 템플릿 + OCR 검증

    Args:
        page_image: 페이지 이미지 (PIL Image)
        page_num: 페이지 번호 (1부터 시작)
        exam: 시험 유형 (CSAT, KICE6, KICE9)
        year: 시험 년도
        verify_ocr: OCR 검증 수행 여부

    Returns:
        List[SplitResult]: 분리된 문제들
    """
    template = get_template(exam, year)
    if not template:
        raise ValueError(f"No template found for {exam}")

    page_template = template.pages.get(page_num)
    if not page_template:
        logger.warning(f"No template for page {page_num}, returning full page")
        return [SplitResult(
            question_no=0,
            image=page_image,
            confidence=0.0,
            needs_review=True,
            review_reason=f"No template for page {page_num}"
        )]

    # Step 1: 템플릿 기반 분리
    crops = template_split(page_image, page_template)
    results = []

    for expected_q, cropped_image in crops:
        result = SplitResult(
            question_no=expected_q,
            image=cropped_image,
            confidence=1.0,
            needs_review=False,
            review_reason=""
        )

        # Step 2: OCR 검증 (선택적)
        if verify_ocr and HAS_TESSERACT:
            detected_q = extract_question_number_ocr(cropped_image)

            if detected_q is None:
                # OCR 실패 - 낮은 신뢰도
                result.confidence = 0.7
                result.needs_review = True
                result.review_reason = "OCR failed to detect question number"

            elif detected_q != expected_q:
                # 문제 번호 불일치 - 수동 검토 필요
                result.confidence = 0.3
                result.needs_review = True
                result.review_reason = f"OCR detected Q{detected_q}, expected Q{expected_q}"
                logger.warning(
                    f"Question number mismatch on page {page_num}: "
                    f"expected Q{expected_q}, detected Q{detected_q}"
                )
            else:
                # 일치 - 높은 신뢰도
                result.confidence = 1.0

        results.append(result)

    return results


# ============================================
# 배치 처리
# ============================================

def process_exam_pdf(
    pdf_pages: List[Image.Image],
    exam: str,
    year: int,
    output_dir: str,
    verify_ocr: bool = True
) -> Dict[str, any]:
    """
    전체 시험지 PDF 처리

    Args:
        pdf_pages: PDF 페이지 이미지 리스트
        exam: 시험 유형
        year: 시험 년도
        output_dir: 출력 디렉토리
        verify_ocr: OCR 검증 수행 여부

    Returns:
        처리 결과 요약
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    all_results = []
    needs_review_list = []

    for page_num, page_image in enumerate(pdf_pages, start=1):
        results = hybrid_split(
            page_image=page_image,
            page_num=page_num,
            exam=exam,
            year=year,
            verify_ocr=verify_ocr
        )

        for result in results:
            # 파일명: {year}_{exam}_Q{question_no:02d}.png
            problem_id = f"{year}_{exam}_Q{result.question_no:02d}"
            filename = f"{problem_id}.png"
            filepath = output_path / filename

            # 이미지 저장
            result.image.save(filepath, "PNG")
            logger.info(f"Saved: {filename} (confidence: {result.confidence:.2f})")

            all_results.append({
                "problem_id": problem_id,
                "page_num": page_num,
                "question_no": result.question_no,
                "confidence": result.confidence,
                "needs_review": result.needs_review,
                "review_reason": result.review_reason,
                "filepath": str(filepath)
            })

            if result.needs_review:
                needs_review_list.append(problem_id)

    # 결과 요약 저장
    summary = {
        "exam": exam,
        "year": year,
        "total_problems": len(all_results),
        "needs_review_count": len(needs_review_list),
        "needs_review": needs_review_list,
        "results": all_results
    }

    summary_path = output_path / "split_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return summary


# ============================================
# 수동 보정 인터페이스
# ============================================

def flag_for_manual_review(problem_id: str, reason: str, review_file: str = "manual_review.json"):
    """수동 검토 필요 문제 플래그"""
    review_path = Path(review_file)

    # 기존 목록 로드
    if review_path.exists():
        with open(review_path, 'r', encoding='utf-8') as f:
            review_list = json.load(f)
    else:
        review_list = []

    # 추가
    review_list.append({
        "problem_id": problem_id,
        "reason": reason,
        "status": "pending"
    })

    # 저장
    with open(review_path, 'w', encoding='utf-8') as f:
        json.dump(review_list, f, ensure_ascii=False, indent=2)

    logger.info(f"Flagged for manual review: {problem_id}")


def update_template_region(
    exam: str,
    page_num: int,
    question_idx: int,
    new_region: CropRegion
):
    """템플릿 영역 수동 조정 (런타임)"""
    template = TEMPLATES.get(exam)
    if template and page_num in template.pages:
        page_template = template.pages[page_num]
        if 0 <= question_idx < len(page_template.regions):
            page_template.regions[question_idx] = new_region
            logger.info(f"Updated region for {exam} page {page_num} Q{question_idx}")


# ============================================
# CLI 인터페이스
# ============================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="KICE Math Page Splitter")
    parser.add_argument("--exam", required=True, choices=["CSAT", "KICE6", "KICE9"])
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--input", required=True, help="Input PDF or image directory")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--no-ocr", action="store_true", help="Skip OCR verification")

    args = parser.parse_args()

    # 예시: 이미지 디렉토리 처리
    input_path = Path(args.input)
    if input_path.is_dir():
        # 이미지 파일들 로드
        image_files = sorted(input_path.glob("*.png")) + sorted(input_path.glob("*.jpg"))
        pdf_pages = [Image.open(f) for f in image_files]

        summary = process_exam_pdf(
            pdf_pages=pdf_pages,
            exam=args.exam,
            year=args.year,
            output_dir=args.output,
            verify_ocr=not args.no_ocr
        )

        print(f"\n=== 처리 완료 ===")
        print(f"총 문제: {summary['total_problems']}")
        print(f"검토 필요: {summary['needs_review_count']}")
        if summary['needs_review']:
            print(f"검토 대상: {', '.join(summary['needs_review'])}")
