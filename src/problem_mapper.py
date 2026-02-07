"""
Problem Mapper Service
Maps PDF pages to individual math problems using configuration and OCR
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()


# Default KICE exam structure (approximate page-to-question mapping)
# This can be overridden with a JSON config file
DEFAULT_MAPPINGS = {
    "CSAT": {
        # 수능 수학 기본 구조 (30문항, 보통 1-2페이지당 1문제)
        "total_questions": 30,
        "page_mapping": {
            # 객관식 1-15번: 보통 앞쪽 페이지
            # 주관식 16-22번 (4점): 중간 페이지
            # 공통과목 후반 + 선택과목: 뒷 페이지
        }
    },
    "KICE6": {
        "total_questions": 30,
        "page_mapping": {}
    },
    "KICE9": {
        "total_questions": 30,
        "page_mapping": {}
    }
}


class ProblemMapper:
    """Map PDF pages to math problems"""

    def __init__(self, config_dir: str = "./config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.mappings = {}

    def load_mapping(self, year: int, exam: str) -> Dict:
        """Load mapping configuration for an exam"""
        config_file = self.config_dir / f"{year}_{exam}_mapping.json"

        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)

        # Return default mapping
        return DEFAULT_MAPPINGS.get(exam, {"total_questions": 30, "page_mapping": {}})

    def save_mapping(self, year: int, exam: str, mapping: Dict):
        """Save mapping configuration"""
        config_file = self.config_dir / f"{year}_{exam}_mapping.json"

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)

        print(f"Saved mapping to {config_file}")

    def create_default_mapping(
        self,
        year: int,
        exam: str,
        image_dir: str,
        questions: int = 30
    ) -> Dict:
        """
        Create a default 1:1 page-to-question mapping

        Args:
            year: Exam year
            exam: Exam type
            image_dir: Directory containing page images
            questions: Total number of questions

        Returns:
            Mapping configuration
        """
        image_path = Path(image_dir)
        images = sorted(image_path.glob("*.png"))

        mapping = {
            "year": year,
            "exam": exam,
            "total_questions": questions,
            "total_pages": len(images),
            "questions": {}
        }

        # Create 1:1 mapping (can be edited later)
        for q_num in range(1, questions + 1):
            mapping["questions"][str(q_num)] = {
                "pages": [q_num] if q_num <= len(images) else [],
                "score": self._default_score(q_num),
                "type": "objective" if q_num <= 15 else "subjective"
            }

        self.save_mapping(year, exam, mapping)
        return mapping

    def _default_score(self, question_no: int) -> int:
        """Get default score for question number"""
        # 수능 배점 기본 규칙
        if question_no <= 15:
            return 2 if question_no <= 6 else 3  # 1-6번 2점, 7-15번 3점
        else:
            return 4  # 16-22번 주관식 4점

    def get_pages_for_question(
        self,
        year: int,
        exam: str,
        question_no: int
    ) -> List[int]:
        """Get page numbers for a specific question"""
        mapping = self.load_mapping(year, exam)
        question_data = mapping.get("questions", {}).get(str(question_no), {})
        return question_data.get("pages", [question_no])

    def get_image_paths_for_question(
        self,
        year: int,
        exam: str,
        question_no: int,
        image_dir: str
    ) -> List[str]:
        """Get image file paths for a specific question"""
        pages = self.get_pages_for_question(year, exam, question_no)
        image_path = Path(image_dir)

        paths = []
        for page in pages:
            # Try different naming patterns
            patterns = [
                f"page_{page:03d}.png",
                f"page_{page:02d}.png",
                f"{year}_{exam}_Q{question_no:02d}.png",
                f"page-{page}.png"
            ]

            for pattern in patterns:
                img_file = image_path / pattern
                if img_file.exists():
                    paths.append(str(img_file))
                    break

        return paths

    def update_question_mapping(
        self,
        year: int,
        exam: str,
        question_no: int,
        pages: List[int],
        score: int = None
    ):
        """Update mapping for a specific question"""
        mapping = self.load_mapping(year, exam)

        if "questions" not in mapping:
            mapping["questions"] = {}

        q_key = str(question_no)
        if q_key not in mapping["questions"]:
            mapping["questions"][q_key] = {}

        mapping["questions"][q_key]["pages"] = pages

        if score is not None:
            mapping["questions"][q_key]["score"] = score

        self.save_mapping(year, exam, mapping)

    def merge_pages_to_single_image(
        self,
        image_paths: List[str],
        output_path: str
    ) -> str:
        """
        Merge multiple page images into a single image (vertical stack)

        Args:
            image_paths: List of image file paths
            output_path: Output file path

        Returns:
            Output file path
        """
        try:
            from PIL import Image
        except ImportError:
            print("PIL not installed. Run: pip install Pillow")
            return image_paths[0] if image_paths else None

        if not image_paths:
            return None

        if len(image_paths) == 1:
            return image_paths[0]

        # Load all images
        images = [Image.open(p) for p in image_paths]

        # Calculate total size
        max_width = max(img.width for img in images)
        total_height = sum(img.height for img in images)

        # Create merged image
        merged = Image.new("RGB", (max_width, total_height), "white")

        y_offset = 0
        for img in images:
            # Center horizontally if narrower
            x_offset = (max_width - img.width) // 2
            merged.paste(img, (x_offset, y_offset))
            y_offset += img.height

        merged.save(output_path)
        print(f"Merged {len(images)} images to {output_path}")

        # Close images
        for img in images:
            img.close()

        return output_path

    def create_question_images(
        self,
        year: int,
        exam: str,
        source_dir: str,
        output_dir: str
    ) -> List[Dict]:
        """
        Create individual question images from page images

        Args:
            year: Exam year
            exam: Exam type
            source_dir: Directory with page images
            output_dir: Directory for question images

        Returns:
            List of created question image info
        """
        mapping = self.load_mapping(year, exam)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = []
        total_questions = mapping.get("total_questions", 30)

        for q_num in range(1, total_questions + 1):
            pages = self.get_pages_for_question(year, exam, q_num)
            image_paths = self.get_image_paths_for_question(year, exam, q_num, source_dir)

            if not image_paths:
                print(f"Warning: No images found for Q{q_num}")
                continue

            # Output filename
            output_file = output_path / f"{year}_{exam}_Q{q_num:02d}.png"

            if len(image_paths) == 1:
                # Single page - just copy/rename
                import shutil
                shutil.copy(image_paths[0], output_file)
            else:
                # Multiple pages - merge
                self.merge_pages_to_single_image(image_paths, str(output_file))

            results.append({
                "question_no": q_num,
                "pages": pages,
                "source_images": image_paths,
                "output_image": str(output_file),
                "score": mapping.get("questions", {}).get(str(q_num), {}).get("score", 3)
            })

            print(f"Created Q{q_num}: {output_file.name}")

        return results


def interactive_mapping(year: int, exam: str, image_dir: str):
    """Interactive tool to create question-to-page mapping"""
    mapper = ProblemMapper()

    print(f"\n=== {year} {exam} 문항 매핑 도구 ===")
    print("명령어:")
    print("  q<번호> p<페이지들>  - 문항에 페이지 할당 (예: q1 p1,2)")
    print("  show               - 현재 매핑 표시")
    print("  save               - 저장")
    print("  quit               - 종료")

    # Load or create default mapping
    mapping = mapper.load_mapping(year, exam)
    if not mapping.get("questions"):
        mapping = mapper.create_default_mapping(year, exam, image_dir)

    while True:
        cmd = input("\n> ").strip().lower()

        if cmd == "quit" or cmd == "q":
            break

        elif cmd == "show":
            for q_num in range(1, mapping.get("total_questions", 30) + 1):
                q_data = mapping.get("questions", {}).get(str(q_num), {})
                pages = q_data.get("pages", [])
                print(f"Q{q_num:02d}: pages {pages}")

        elif cmd == "save":
            mapper.save_mapping(year, exam, mapping)
            print("Saved!")

        elif cmd.startswith("q"):
            # Parse: q1 p1,2 or q1 p1-3
            match = re.match(r"q(\d+)\s+p([\d,\-]+)", cmd)
            if match:
                q_num = int(match.group(1))
                pages_str = match.group(2)

                # Parse pages
                pages = []
                for part in pages_str.split(","):
                    if "-" in part:
                        start, end = map(int, part.split("-"))
                        pages.extend(range(start, end + 1))
                    else:
                        pages.append(int(part))

                if "questions" not in mapping:
                    mapping["questions"] = {}

                mapping["questions"][str(q_num)] = {
                    "pages": pages,
                    "score": mapper._default_score(q_num)
                }
                print(f"Q{q_num} -> pages {pages}")
            else:
                print("형식: q<번호> p<페이지들> (예: q1 p1,2 또는 q5 p3-5)")

        else:
            print("Unknown command")


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 4:
        year = int(sys.argv[1])
        exam = sys.argv[2]
        image_dir = sys.argv[3]
        interactive_mapping(year, exam, image_dir)
    else:
        print("Usage: python problem_mapper.py <year> <exam> <image_dir>")
        print("Example: python problem_mapper.py 2026 CSAT ./output/2026_CSAT_PROBLEM")
