"""
Notion 연동 서비스
- 검수 데이터베이스 관리
- 문제 카드 생성/조회/수정
- 상태 동기화
"""

from typing import Optional
from datetime import datetime

from notion_client import Client

from .config import NOTION_TOKEN, NOTION_DATABASE_ID


class NotionService:
    """Notion API 서비스"""

    def __init__(self, token: Optional[str] = None, database_id: Optional[str] = None):
        """
        Args:
            token: Notion Internal Integration Token
            database_id: 데이터베이스 ID
        """
        self.token = token or NOTION_TOKEN
        self.database_id = database_id or NOTION_DATABASE_ID
        self.client = Client(auth=self.token)

        print("Notion 연결 성공!")

    def create_problem_card(self, problem_data: dict) -> dict:
        """
        문제 검수용 카드 생성

        Args:
            problem_data: 문제 데이터
                - problem_id: 문제 ID (필수)
                - year: 연도
                - exam: 시험 유형 (CSAT, KICE6, KICE9)
                - question_no: 문항 번호
                - score: 배점
                - source_url: 원본 PDF 링크
                - image_folder_url: 이미지 폴더 링크
                - extract_text: 추출된 텍스트

        Returns:
            생성된 페이지 정보
        """
        properties = {
            "문제 ID": {
                "title": [{"text": {"content": problem_data.get("problem_id", "")}}]
            },
        }

        # 연도
        if problem_data.get("year"):
            properties["연도"] = {"number": problem_data["year"]}

        # 시험 유형
        if problem_data.get("exam"):
            properties["시험"] = {"select": {"name": problem_data["exam"]}}

        # 문항 번호
        if problem_data.get("question_no"):
            properties["문항번호"] = {"number": problem_data["question_no"]}

        # 배점
        if problem_data.get("score"):
            properties["배점"] = {"number": problem_data["score"]}

        # 상태 (기본값: 검수 필요)
        properties["상태"] = {"select": {"name": "검수 필요"}}

        # 원본 링크
        if problem_data.get("source_url"):
            properties["원본링크"] = {"url": problem_data["source_url"]}

        # 이미지 폴더 링크
        if problem_data.get("image_folder_url"):
            properties["이미지폴더"] = {"url": problem_data["image_folder_url"]}

        # 생성 요청
        response = self.client.pages.create(
            parent={"database_id": self.database_id},
            properties=properties,
        )

        # 추출된 텍스트가 있으면 본문에 추가
        if problem_data.get("extract_text"):
            self._add_content_to_page(
                response["id"],
                problem_data["extract_text"]
            )

        print(f"Notion 카드 생성: {problem_data.get('problem_id')}")
        return response

    def _add_content_to_page(self, page_id: str, content: str):
        """페이지 본문에 콘텐츠 추가"""
        # 내용을 블록 단위로 분할 (2000자 제한)
        max_length = 2000
        chunks = [content[i:i+max_length] for i in range(0, len(content), max_length)]

        blocks = []
        for chunk in chunks:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                }
            })

        if blocks:
            self.client.blocks.children.append(
                block_id=page_id,
                children=blocks
            )

    def query_problems(
        self,
        status: Optional[str] = None,
        year: Optional[int] = None,
        exam: Optional[str] = None,
    ) -> list:
        """
        문제 목록 조회

        Args:
            status: 상태 필터 (검수 필요, 검수 완료, 발송 준비 등)
            year: 연도 필터
            exam: 시험 유형 필터

        Returns:
            문제 목록
        """
        filters = []

        if status:
            filters.append({
                "property": "상태",
                "select": {"equals": status}
            })

        if year:
            filters.append({
                "property": "연도",
                "number": {"equals": year}
            })

        if exam:
            filters.append({
                "property": "시험",
                "select": {"equals": exam}
            })

        query_params = {"database_id": self.database_id}

        if len(filters) == 1:
            query_params["filter"] = filters[0]
        elif len(filters) > 1:
            query_params["filter"] = {"and": filters}

        response = self.client.databases.query(**query_params)
        return response.get("results", [])

    def get_ready_problems(self) -> list:
        """검수 완료된 문제 목록 조회"""
        return self.query_problems(status="검수 완료")

    def get_pending_problems(self) -> list:
        """검수 필요한 문제 목록 조회"""
        return self.query_problems(status="검수 필요")

    def update_problem_status(
        self,
        page_id: str,
        status: str,
        additional_data: Optional[dict] = None
    ) -> dict:
        """
        문제 상태 업데이트

        Args:
            page_id: Notion 페이지 ID
            status: 새 상태
            additional_data: 추가 업데이트 데이터

        Returns:
            업데이트된 페이지 정보
        """
        properties = {
            "상태": {"select": {"name": status}}
        }

        if additional_data:
            # 과목
            if additional_data.get("subject"):
                properties["과목"] = {"select": {"name": additional_data["subject"]}}

            # 단원
            if additional_data.get("unit"):
                properties["단원"] = {"select": {"name": additional_data["unit"]}}

            # 정답
            if additional_data.get("answer"):
                properties["정답"] = {
                    "rich_text": [{"text": {"content": str(additional_data["answer"])}}]
                }

            # 출제 의도
            if additional_data.get("intent"):
                properties["출제의도"] = {
                    "rich_text": [{"text": {"content": additional_data["intent"]}}]
                }

        response = self.client.pages.update(
            page_id=page_id,
            properties=properties
        )

        print(f"상태 업데이트: {page_id} -> {status}")
        return response

    def get_page_content(self, page_id: str) -> dict:
        """페이지 전체 내용 조회"""
        # 페이지 속성
        page = self.client.pages.retrieve(page_id=page_id)

        # 페이지 본문
        blocks = self.client.blocks.children.list(block_id=page_id)

        return {
            "properties": page["properties"],
            "content": blocks.get("results", [])
        }

    def parse_properties(self, page: dict) -> dict:
        """
        Notion 페이지 속성을 딕셔너리로 파싱

        Args:
            page: Notion 페이지 객체

        Returns:
            파싱된 속성 딕셔너리
        """
        props = page.get("properties", {})
        result = {
            "page_id": page["id"],
        }

        for key, value in props.items():
            prop_type = value.get("type")

            if prop_type == "title":
                title_content = value.get("title", [])
                result[key] = title_content[0]["text"]["content"] if title_content else ""

            elif prop_type == "number":
                result[key] = value.get("number")

            elif prop_type == "select":
                select_data = value.get("select")
                result[key] = select_data["name"] if select_data else None

            elif prop_type == "multi_select":
                multi = value.get("multi_select", [])
                result[key] = [item["name"] for item in multi]

            elif prop_type == "rich_text":
                rich_text = value.get("rich_text", [])
                result[key] = rich_text[0]["text"]["content"] if rich_text else ""

            elif prop_type == "url":
                result[key] = value.get("url")

            elif prop_type == "checkbox":
                result[key] = value.get("checkbox", False)

            elif prop_type == "date":
                date_data = value.get("date")
                if date_data:
                    result[key] = date_data.get("start")
                else:
                    result[key] = None

        return result

    def sync_to_supabase(self, supabase_service) -> list:
        """
        검수 완료된 문제를 Supabase로 동기화

        Args:
            supabase_service: SupabaseService 인스턴스

        Returns:
            동기화된 문제 목록
        """
        ready_problems = self.get_ready_problems()
        synced = []

        for page in ready_problems:
            try:
                data = self.parse_properties(page)

                # Supabase에 업데이트
                result = supabase_service.update_problem_from_notion(data)

                if result:
                    # Notion 상태 업데이트
                    self.update_problem_status(page["id"], "발송 준비")
                    synced.append(data)

            except Exception as e:
                print(f"동기화 실패: {data.get('문제 ID')} - {e}")

        print(f"Supabase 동기화 완료: {len(synced)}개")
        return synced


# 편의 함수
def get_notion_service() -> NotionService:
    """NotionService 인스턴스 반환"""
    return NotionService()


if __name__ == "__main__":
    # 테스트
    service = NotionService()

    print("\n=== 검수 필요 문제 ===")
    pending = service.get_pending_problems()
    for page in pending[:3]:
        data = service.parse_properties(page)
        print(f"- {data.get('문제 ID', 'N/A')}")
