"""
KICE 수학 정답 PDF 파서
PyMuPDF를 사용해 정답표 PDF에서 정답/배점을 추출합니다.

지원 형식:
- 2026학년도 수능 수학 정답표 (홀수/짝수형)
- 공통과목 Q1-Q22 + 선택과목 (확률과통계/미적분/기하) Q23-Q30
"""

import re
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF


class AnswerParser:
    """KICE 수학 정답 PDF 파서"""

    CIRCLE_MAP = {"①": 1, "②": 2, "③": 3, "④": 4, "⑤": 5}

    # 헤더 텍스트 패턴 (필터링 대상)
    HEADER_PATTERNS = [
        "학년도", "대학수학능력시험", "수학 영역", "정답표",
        "홀수", "짝수", "공통", "선택", "확률과 통계", "미적분", "기하",
        "문항", "번호", "정답", "배점",
    ]

    def parse_pdf(self, pdf_path: str, page: int = 0) -> dict:
        """
        정답 PDF 파싱

        Args:
            pdf_path: PDF 파일 경로
            page: 파싱할 페이지 (0=홀수형, 1=짝수형)

        Returns:
            {
                'form': '홀수' | '짝수',
                'common': {1: (answer, score), 2: (answer, score), ..., 22: (answer, score)},
                'electives': {
                    '확률과통계': {23: (answer, score), ..., 30: (answer, score)},
                    '미적분': {23: (answer, score), ..., 30: (answer, score)},
                    '기하': {23: (answer, score), ..., 30: (answer, score)},
                }
            }
        """
        text = self._extract_text(pdf_path, page)
        return self._parse_table(text)

    def _extract_text(self, pdf_path: str, page: int = 0) -> str:
        """PyMuPDF로 PDF 텍스트 추출"""
        doc = fitz.open(str(pdf_path))
        if page >= len(doc):
            raise ValueError(f"페이지 {page}가 없습니다 (총 {len(doc)}페이지)")
        text = doc[page].get_text()
        doc.close()
        return text

    def _is_header_line(self, line: str) -> bool:
        """헤더/메타데이터 줄인지 판별"""
        for pattern in self.HEADER_PATTERNS:
            if pattern in line:
                return True
        return False

    def _normalize_answer(self, raw: str) -> int:
        """정답 정규화: ①→1, 숫자 문자열→int"""
        raw = raw.strip()
        if raw in self.CIRCLE_MAP:
            return self.CIRCLE_MAP[raw]
        try:
            return int(raw)
        except ValueError:
            raise ValueError(f"인식할 수 없는 정답: '{raw}'")

    def _parse_table(self, text: str) -> dict:
        """
        텍스트를 파싱하여 정답 딕셔너리 생성

        테이블 구조 (5열):
        - 열1: 공통 Q1-Q11 (문항번호, 정답, 배점)
        - 열2: 공통 Q12-Q22
        - 열3: 확률과통계 Q23-Q30
        - 열4: 미적분 Q23-Q30
        - 열5: 기하 Q23-Q30

        텍스트 추출 순서: 행 단위로 5열씩 읽힘
        - 행 1-8: 5열 × 3값 = 15개 토큰
        - 행 9-11: 2열 × 3값 = 6개 토큰
        """
        form = "홀수" if "홀수" in text else "짝수"

        # 텍스트를 줄 단위로 분리하고 헤더 제거
        lines = text.strip().split("\n")
        tokens = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if self._is_header_line(line):
                continue
            # 한 줄에 여러 값이 붙어있는 경우 분리 (예: "번호정답배점")
            # 순수 숫자 또는 원문자만 토큰으로 추가
            if re.match(r'^[①②③④⑤]$', line) or re.match(r'^\d+$', line):
                tokens.append(line)
            else:
                # 혹시 "번호정답배점문항" 같은 합쳐진 헤더가 남아있으면 스킵
                continue

        # 토큰을 3개씩 그룹화 (문항번호, 정답, 배점)
        triplets = []
        for i in range(0, len(tokens) - 2, 3):
            try:
                q_no = int(tokens[i])
                answer = self._normalize_answer(tokens[i + 1])
                score = int(tokens[i + 2])
                triplets.append((q_no, answer, score))
            except (ValueError, IndexError):
                continue

        # 테이블 구조에 따라 분배
        # 행 1-8: 5 triplets per row (공통1, 공통2, 확통, 미적, 기하)
        # 행 9-11: 2 triplets per row (공통1, 공통2)
        common = {}
        electives = {"확률과통계": {}, "미적분": {}, "기하": {}}

        idx = 0
        # 행 1-8 (5열)
        for row in range(8):
            if idx + 5 > len(triplets):
                break
            q1_no, q1_ans, q1_score = triplets[idx]      # 공통1 (Q1-Q8)
            q2_no, q2_ans, q2_score = triplets[idx + 1]  # 공통2 (Q12-Q19)
            e1_no, e1_ans, e1_score = triplets[idx + 2]  # 확률과통계
            e2_no, e2_ans, e2_score = triplets[idx + 3]  # 미적분
            e3_no, e3_ans, e3_score = triplets[idx + 4]  # 기하
            idx += 5

            common[q1_no] = (q1_ans, q1_score)
            common[q2_no] = (q2_ans, q2_score)
            electives["확률과통계"][e1_no] = (e1_ans, e1_score)
            electives["미적분"][e2_no] = (e2_ans, e2_score)
            electives["기하"][e3_no] = (e3_ans, e3_score)

        # 행 9-11 (2열만)
        for row in range(3):
            if idx + 2 > len(triplets):
                break
            q1_no, q1_ans, q1_score = triplets[idx]
            q2_no, q2_ans, q2_score = triplets[idx + 1]
            idx += 2

            common[q1_no] = (q1_ans, q1_score)
            common[q2_no] = (q2_ans, q2_score)

        return {
            "form": form,
            "common": common,
            "electives": electives,
        }

    def get_answer_type(self, question_no: int) -> str:
        """문항 번호로 정답 유형 판별"""
        if 1 <= question_no <= 15:
            return "multiple"
        elif 16 <= question_no <= 22:
            return "short"
        elif 23 <= question_no <= 28:
            return "multiple"
        elif 29 <= question_no <= 30:
            return "short"
        return "multiple"

    def to_db_records(
        self,
        parsed: dict,
        year: int,
        exam: str,
        elective: str = "확률과통계",
    ) -> list:
        """
        파싱 결과를 DB 업데이트용 레코드 리스트로 변환

        Args:
            parsed: parse_pdf() 결과
            year: 시험 년도
            exam: 시험 유형 (CSAT, KICE6, KICE9)
            elective: 선택과목 ('확률과통계', '미적분', '기하')

        Returns:
            [
                {
                    'problem_id': '2026_CSAT_Q01',
                    'answer': 1,
                    'answer_verified': 1,
                    'score': 2,
                    'score_verified': 2,
                    'answer_type': 'multiple',
                },
                ...
            ]
        """
        records = []

        # 공통과목 Q1-Q22
        for q_no, (answer, score) in sorted(parsed["common"].items()):
            records.append({
                "problem_id": f"{year}_{exam}_Q{q_no:02d}",
                "answer": answer,
                "answer_verified": answer,
                "score": score,
                "score_verified": score,
                "answer_type": self.get_answer_type(q_no),
            })

        # 선택과목 Q23-Q30
        if elective in parsed["electives"]:
            for q_no, (answer, score) in sorted(parsed["electives"][elective].items()):
                records.append({
                    "problem_id": f"{year}_{exam}_Q{q_no:02d}",
                    "answer": answer,
                    "answer_verified": answer,
                    "score": score,
                    "score_verified": score,
                    "answer_type": self.get_answer_type(q_no),
                })

        return records

    def print_summary(self, parsed: dict):
        """파싱 결과 요약 출력"""
        print(f"\n  정답표 형태: {parsed['form']}형")
        print(f"  공통과목: {len(parsed['common'])}문항")
        for name, data in parsed["electives"].items():
            print(f"  {name}: {len(data)}문항")

        print("\n  공통과목 정답:")
        for q_no in sorted(parsed["common"]):
            ans, score = parsed["common"][q_no]
            print(f"    Q{q_no:02d}: 정답={ans}, 배점={score}")

        for name, data in parsed["electives"].items():
            print(f"\n  {name} 정답:")
            for q_no in sorted(data):
                ans, score = data[q_no]
                print(f"    Q{q_no:02d}: 정답={ans}, 배점={score}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("사용법: python -m src.answer_parser <pdf_path>")
        sys.exit(1)

    parser = AnswerParser()
    result = parser.parse_pdf(sys.argv[1])
    parser.print_summary(result)
