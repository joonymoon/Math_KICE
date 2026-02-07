"""
Supabase 연동 서비스
- 문제 데이터 CRUD
- 자동 추출 데이터 저장
- Notion 검수 결과 동기화
"""

import re
from typing import Optional
from datetime import datetime

from supabase import create_client, Client

from .config import SUPABASE_URL, SUPABASE_KEY


class SupabaseService:
    """Supabase 데이터베이스 서비스"""

    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        Args:
            url: Supabase 프로젝트 URL
            key: Supabase anon key
        """
        self.url = url or SUPABASE_URL
        self.key = key or SUPABASE_KEY
        self.client: Client = create_client(self.url, self.key)

        print("Supabase 연결 성공!")

    # ============================================
    # 문제 관리
    # ============================================

    def create_problem(self, problem_data: dict) -> dict:
        """
        새 문제 생성

        Args:
            problem_data: 문제 데이터
                - problem_id: 문제 ID (필수, 예: 2024_CSAT_Q13)
                - year: 연도
                - exam: 시험 유형
                - question_no: 문항 번호
                - score: 배점
                - extract_text: 추출된 텍스트
                - source_ref: 원본 PDF 링크
                - page_images_folder: 이미지 폴더 링크

        Returns:
            생성된 문제 데이터
        """
        response = self.client.table("problems").insert(problem_data).execute()

        if response.data:
            print(f"문제 생성: {problem_data.get('problem_id')}")
            return response.data[0]

        return None

    def upsert_problem(self, problem_data: dict) -> dict:
        """
        문제 생성 또는 업데이트 (problem_id 기준)

        Args:
            problem_data: 문제 데이터 (problem_id 필수)

        Returns:
            생성/업데이트된 문제 데이터
        """
        # updated_at 갱신
        problem_data["updated_at"] = datetime.now().isoformat()

        response = self.client.table("problems").upsert(
            problem_data,
            on_conflict="problem_id"
        ).execute()

        if response.data:
            print(f"문제 upsert: {problem_data.get('problem_id')}")
            return response.data[0]

        return None

    def get_problem(self, problem_id: str) -> Optional[dict]:
        """문제 조회"""
        response = self.client.table("problems") \
            .select("*") \
            .eq("problem_id", problem_id) \
            .single() \
            .execute()

        return response.data

    def get_problems_by_filter(
        self,
        year: Optional[int] = None,
        exam: Optional[str] = None,
        status: Optional[str] = None,
        subject: Optional[str] = None,
        score: Optional[int] = None,
        limit: int = 500,
    ) -> list:
        """
        조건별 문제 목록 조회

        Args:
            year: 연도 필터
            exam: 시험 유형 필터 (CSAT, KICE6, KICE9)
            status: 상태 필터 (needs_review, ready, hold, inactive)
            subject: 과목 필터 (Math1, Math2)
            score: 난이도 필터 (2, 3, 4점)
            limit: 최대 결과 수

        Returns:
            문제 목록
        """
        query = self.client.table("problems").select("*")

        if year:
            query = query.eq("year", year)
        if exam:
            query = query.eq("exam", exam)
        if status:
            query = query.eq("status", status)
        if subject:
            query = query.eq("subject", subject)
        if score:
            query = query.eq("score", score)

        response = query.order("year", desc=True) \
            .order("exam") \
            .order("question_no") \
            .limit(limit) \
            .execute()

        return response.data

    def get_problems_to_review(self) -> list:
        """검수 필요한 문제 목록"""
        return self.get_problems_by_filter(status="needs_review")

    def get_ready_problems(self) -> list:
        """발송 가능한 문제 목록"""
        return self.get_problems_by_filter(status="ready")

    def update_problem(self, problem_id: str, update_data: dict) -> dict:
        """
        문제 업데이트

        Args:
            problem_id: 문제 ID
            update_data: 업데이트할 데이터

        Returns:
            업데이트된 문제 데이터
        """
        update_data["updated_at"] = datetime.now().isoformat()

        response = self.client.table("problems") \
            .update(update_data) \
            .eq("problem_id", problem_id) \
            .execute()

        if response.data:
            print(f"문제 업데이트: {problem_id}")
            return response.data[0]

        return None

    def update_problem_from_notion(self, notion_data: dict) -> dict:
        """
        Notion 검수 결과를 Supabase에 반영

        Args:
            notion_data: Notion에서 파싱된 데이터

        Returns:
            업데이트된 문제 데이터
        """
        problem_id = notion_data.get("문제 ID")
        if not problem_id:
            print("문제 ID가 없습니다.")
            return None

        update_data = {
            "status": "ready",
        }

        # 과목
        if notion_data.get("과목"):
            update_data["subject"] = notion_data["과목"]

        # 단원
        if notion_data.get("단원"):
            update_data["unit"] = notion_data["단원"]

        # 정답 (검수 확정)
        if notion_data.get("정답"):
            update_data["answer_verified"] = str(notion_data["정답"])

        # 배점 (검수 확정)
        if notion_data.get("배점"):
            update_data["score_verified"] = notion_data["배점"]

        # 출제 의도
        if notion_data.get("출제의도"):
            update_data["intent_1"] = notion_data["출제의도"]

        # 난이도
        if notion_data.get("난이도"):
            update_data["difficulty"] = notion_data["난이도"]

        # Notion 페이지 ID 저장
        if notion_data.get("page_id"):
            update_data["notion_page_id"] = notion_data["page_id"]

        return self.update_problem(problem_id, update_data)

    # ============================================
    # 힌트 관리
    # ============================================

    def create_hint(
        self,
        problem_id: str,
        stage: int,
        hint_type: str,
        hint_text: str
    ) -> dict:
        """
        힌트 생성

        Args:
            problem_id: 문제 ID
            stage: 힌트 단계 (1, 2, 3)
            hint_type: 힌트 유형
                - concept_direction: 개념 방향
                - key_transformation: 핵심 전환
                - decisive_line: 결정적 한 줄
            hint_text: 힌트 내용

        Returns:
            생성된 힌트 데이터
        """
        hint_data = {
            "problem_id": problem_id,
            "stage": stage,
            "hint_type": hint_type,
            "hint_text": hint_text,
        }

        response = self.client.table("hints").upsert(
            hint_data,
            on_conflict="problem_id,stage"
        ).execute()

        if response.data:
            print(f"힌트 생성: {problem_id} 단계 {stage}")
            return response.data[0]

        return None

    def get_hints(self, problem_id: str) -> list:
        """문제의 힌트 목록 조회"""
        response = self.client.table("hints") \
            .select("*") \
            .eq("problem_id", problem_id) \
            .order("stage") \
            .execute()

        return response.data

    # ============================================
    # 처리 이력 관리
    # ============================================

    def get_processed_file_ids(self) -> set:
        """이미 처리된 파일 ID 목록 조회"""
        response = self.client.table("problems") \
            .select("source_ref") \
            .not_.is_("source_ref", "null") \
            .execute()

        # source_ref에서 파일 ID 추출
        file_ids = set()
        for row in response.data:
            source_ref = row.get("source_ref", "")
            # URL에서 파일 ID 추출 (간단한 방법)
            if "drive.google.com" in source_ref:
                # /d/FILE_ID/ 또는 id=FILE_ID 형식
                match = re.search(r'/d/([a-zA-Z0-9_-]+)', source_ref)
                if match:
                    file_ids.add(match.group(1))
                else:
                    match = re.search(r'id=([a-zA-Z0-9_-]+)', source_ref)
                    if match:
                        file_ids.add(match.group(1))

        return file_ids

    # ============================================
    # 통계
    # ============================================

    def get_stats(self) -> dict:
        """문제 통계 조회"""
        all_problems = self.client.table("problems") \
            .select("status, year, exam") \
            .execute()

        stats = {
            "total": len(all_problems.data),
            "by_status": {},
            "by_year": {},
            "by_exam": {},
        }

        for problem in all_problems.data:
            # 상태별
            status = problem.get("status", "unknown")
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

            # 연도별
            year = problem.get("year")
            if year:
                stats["by_year"][year] = stats["by_year"].get(year, 0) + 1

            # 시험별
            exam = problem.get("exam")
            if exam:
                stats["by_exam"][exam] = stats["by_exam"].get(exam, 0) + 1

        return stats

    def print_stats(self):
        """통계 출력"""
        stats = self.get_stats()

        print("\n" + "=" * 50)
        print("KICE 수학 문제 통계")
        print("=" * 50)
        print(f"총 문제 수: {stats['total']}")

        print("\n상태별:")
        for status, count in stats["by_status"].items():
            print(f"  {status}: {count}")

        print("\n연도별:")
        for year, count in sorted(stats["by_year"].items(), reverse=True):
            print(f"  {year}: {count}")

        print("\n시험별:")
        for exam, count in stats["by_exam"].items():
            print(f"  {exam}: {count}")

        print("=" * 50)


# 편의 함수
def get_supabase_service() -> SupabaseService:
    """SupabaseService 인스턴스 반환"""
    return SupabaseService()


if __name__ == "__main__":
    # 테스트
    service = SupabaseService()
    service.print_stats()
