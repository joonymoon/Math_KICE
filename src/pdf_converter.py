"""
PDF 변환 서비스
- PDF → PNG 이미지 변환
- PDF 텍스트 추출
- CloudConvert 없이 로컬에서 처리
"""

import re
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

from .config import OUTPUT_PATH, PDF_DPI


class PDFConverter:
    """PDF 변환 및 처리"""

    def __init__(self, dpi: int = PDF_DPI):
        """
        Args:
            dpi: 이미지 해상도 (기본값: 200)
        """
        self.dpi = dpi
        self.zoom = dpi / 72  # 72 DPI 기준

    def pdf_to_images(
        self,
        pdf_path: Path,
        output_folder: Optional[Path] = None,
        page_range: Optional[tuple] = None,
    ) -> list:
        """
        PDF를 PNG 이미지로 변환

        Args:
            pdf_path: PDF 파일 경로
            output_folder: 출력 폴더 (없으면 기본 OUTPUT_PATH 사용)
            page_range: 페이지 범위 (시작, 끝) - 1부터 시작

        Returns:
            생성된 이미지 파일 경로 목록
        """
        output_folder = output_folder or OUTPUT_PATH
        output_folder.mkdir(parents=True, exist_ok=True)

        # PDF 파일명으로 하위 폴더 생성
        pdf_name = pdf_path.stem
        image_folder = output_folder / pdf_name
        image_folder.mkdir(parents=True, exist_ok=True)

        doc = fitz.open(pdf_path)
        images = []

        # 페이지 범위 설정
        start_page = 0
        end_page = len(doc)

        if page_range:
            start_page = max(0, page_range[0] - 1)  # 1-indexed to 0-indexed
            end_page = min(len(doc), page_range[1])

        print(f"PDF 변환 시작: {pdf_path.name} ({end_page - start_page}페이지)")

        for page_num in range(start_page, end_page):
            page = doc[page_num]

            # 이미지 렌더링
            mat = fitz.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=mat)

            # 파일 저장
            output_path = image_folder / f"page_{page_num + 1:03d}.png"
            pix.save(str(output_path))

            images.append(output_path)
            print(f"  페이지 {page_num + 1}/{end_page}: {output_path.name}")

        doc.close()
        print(f"PDF 변환 완료: {len(images)}개 이미지 생성")

        return images

    def extract_text(self, pdf_path: Path, page_range: Optional[tuple] = None) -> str:
        """
        PDF에서 텍스트 추출

        Args:
            pdf_path: PDF 파일 경로
            page_range: 페이지 범위 (시작, 끝) - 1부터 시작

        Returns:
            추출된 텍스트
        """
        doc = fitz.open(pdf_path)
        text_parts = []

        start_page = 0
        end_page = len(doc)

        if page_range:
            start_page = max(0, page_range[0] - 1)
            end_page = min(len(doc), page_range[1])

        for page_num in range(start_page, end_page):
            page = doc[page_num]
            text = page.get_text()
            text_parts.append(f"=== 페이지 {page_num + 1} ===\n{text}")

        doc.close()

        return "\n\n".join(text_parts)

    def extract_problem_info(self, text: str) -> dict:
        """
        추출된 텍스트에서 문제 정보 파싱

        Args:
            text: PDF에서 추출한 텍스트

        Returns:
            파싱된 정보 딕셔너리
        """
        info = {
            "question_numbers": [],
            "scores": [],
            "answers": [],
        }

        # 문항 번호 추출 (예: "13.", "13번", "[13]")
        question_pattern = r'[\[\(]?(\d{1,2})[\]\)]?[\.\s번]'
        questions = re.findall(question_pattern, text)
        info["question_numbers"] = [int(q) for q in questions]

        # 배점 추출 (예: "[3점]", "(4점)", "3점")
        score_pattern = r'[\[\(]?([234])점[\]\)]?'
        scores = re.findall(score_pattern, text)
        info["scores"] = [int(s) for s in scores]

        # 정답 추출 (정답표에서)
        # 패턴: "13 ③" 또는 "13번 3" 또는 "13: 3"
        answer_pattern = r'(\d{1,2})\s*[:\s번]?\s*[①②③④⑤]?(\d)'
        answers = re.findall(answer_pattern, text)
        info["answers"] = [(int(q), int(a)) for q, a in answers]

        return info

    def get_page_count(self, pdf_path: Path) -> int:
        """PDF 페이지 수 반환"""
        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        return count

    def extract_single_page(
        self,
        pdf_path: Path,
        page_number: int,
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        단일 페이지 이미지 추출

        Args:
            pdf_path: PDF 파일 경로
            page_number: 페이지 번호 (1부터 시작)
            output_path: 출력 파일 경로

        Returns:
            생성된 이미지 파일 경로
        """
        doc = fitz.open(pdf_path)

        if page_number < 1 or page_number > len(doc):
            raise ValueError(f"잘못된 페이지 번호: {page_number} (총 {len(doc)}페이지)")

        page = doc[page_number - 1]
        mat = fitz.Matrix(self.zoom, self.zoom)
        pix = page.get_pixmap(matrix=mat)

        if not output_path:
            output_path = OUTPUT_PATH / f"{pdf_path.stem}_page_{page_number:03d}.png"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(output_path))

        doc.close()
        print(f"페이지 {page_number} 추출: {output_path}")

        return output_path


def parse_filename(filename: str) -> dict:
    """
    파일명에서 메타데이터 추출

    Args:
        filename: 파일명 (예: "2024_CSAT_PROBLEM.pdf")

    Returns:
        추출된 정보 딕셔너리
    """
    import re
    from .config import FILENAME_PATTERN, EXAM_TYPE_MAP

    result = {
        "year": None,
        "exam": None,
        "exam_korean": None,
        "file_type": None,
        "original_filename": filename,
    }

    # 확장자 제거
    name_without_ext = Path(filename).stem

    # 패턴 매칭
    match = re.match(FILENAME_PATTERN, filename)
    if match:
        result["year"] = int(match.group(1))
        result["exam"] = match.group(2)
        result["exam_korean"] = EXAM_TYPE_MAP.get(match.group(2), match.group(2))
        result["file_type"] = match.group(3)
    else:
        # 대안 패턴: 연도만 추출
        year_match = re.search(r'(20\d{2})', filename)
        if year_match:
            result["year"] = int(year_match.group(1))

        # 시험 유형 추출
        for exam_code in EXAM_TYPE_MAP.keys():
            if exam_code in filename.upper():
                result["exam"] = exam_code
                result["exam_korean"] = EXAM_TYPE_MAP[exam_code]
                break

    return result


# 편의 함수
def convert_pdf(pdf_path: Path, dpi: int = 200) -> list:
    """PDF를 이미지로 변환하는 간단한 함수"""
    converter = PDFConverter(dpi=dpi)
    return converter.pdf_to_images(pdf_path)


if __name__ == "__main__":
    # 테스트
    print("PDF 변환 테스트")

    # 파일명 파싱 테스트
    test_files = [
        "2024_CSAT_PROBLEM.pdf",
        "2023_KICE6_ANSWER.pdf",
        "2022_KICE9_PROBLEM.pdf",
    ]

    for filename in test_files:
        info = parse_filename(filename)
        print(f"{filename} -> {info}")
