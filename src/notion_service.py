"""
Notion 연동 서비스
- 검수 데이터베이스 관리
- 문제 카드 생성/조회/수정
- 상태 동기화
"""

import re
import time
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
        # notion-client 2.7.0 has invalid default version (2025-09-03), use stable version
        self.client = Client(auth=self.token, notion_version="2022-06-28")

        print("Notion 연결 성공!")

    def _api_call_with_retry(self, func, *args, max_retries=3, **kwargs):
        """API 호출 with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt < max_retries - 1 and "rate" in str(e).lower():
                    wait = 2 ** (attempt + 1)
                    print(f"  Rate limit, {wait}초 대기 후 재시도...")
                    time.sleep(wait)
                else:
                    raise

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

        query_body = {}

        if len(filters) == 1:
            query_body["filter"] = filters[0]
        elif len(filters) > 1:
            query_body["filter"] = {"and": filters}

        # notion-client 2.x: databases.query() removed, use request() directly
        # Pagination: Notion API returns max 100 results per page
        all_results = []
        has_more = True
        next_cursor = None

        while has_more:
            page_body = dict(query_body)
            if next_cursor:
                page_body["start_cursor"] = next_cursor

            response = self.client.request(
                path=f"databases/{self.database_id}/query",
                method="POST",
                body=page_body
            )
            all_results.extend(response.get("results", []))
            has_more = response.get("has_more", False)
            next_cursor = response.get("next_cursor")

        return all_results

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
                result[key] = "".join(rt.get("text", {}).get("content", "") for rt in rich_text) if rich_text else ""

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

    # ============================================
    # 검수 페이지 생성
    # ============================================

    def create_review_page(self, problem: dict, hints: list) -> dict:
        """
        문제 검수용 풍부한 페이지 생성/업데이트

        Args:
            problem: Supabase problems 테이블 전체 데이터
            hints: Supabase hints 테이블 데이터 리스트

        Returns:
            생성/업데이트된 페이지 정보
        """
        problem_id = problem["problem_id"]

        # Notion 속성 설정
        properties = {
            "문제 ID": {"title": [{"text": {"content": problem_id}}]},
            "상태": {"select": {"name": "검수 필요"}},
        }
        if problem.get("year"):
            properties["연도"] = {"number": problem["year"]}
        if problem.get("exam"):
            properties["시험"] = {"select": {"name": problem["exam"]}}
        if problem.get("question_no"):
            properties["문항번호"] = {"number": problem["question_no"]}
        if problem.get("score"):
            properties["배점"] = {"number": problem["score"]}
        if problem.get("subject"):
            properties["과목"] = {"select": {"name": problem["subject"]}}
        if problem.get("unit"):
            properties["단원"] = {"select": {"name": problem["unit"]}}
        if problem.get("answer") is not None:
            properties["정답"] = {
                "rich_text": [{"text": {"content": str(problem["answer"])}}]
            }
        if problem.get("intent_1"):
            properties["출제의도"] = {
                "rich_text": [{"text": {"content": problem["intent_1"][:2000]}}]
            }
        if problem.get("problem_image_url"):
            properties["원본링크"] = {"url": problem["problem_image_url"]}
        if problem.get("solution"):
            properties["풀이"] = {
                "rich_text": [{"text": {"content": problem["solution"][:2000]}}]
            }
        # 난이도
        if problem.get("difficulty"):
            properties["난이도"] = {"number": problem["difficulty"]}
        # 정답유형
        answer_type_kr = "객관식" if problem.get("answer_type") == "multiple" else "주관식"
        properties["정답유형"] = {"select": {"name": answer_type_kr}}

        # 힌트 속성 설정
        hints_by_stage = {h["stage"]: h for h in hints}
        for stage, prop_name in [(1, "힌트1"), (2, "힌트2"), (3, "힌트3")]:
            hint = hints_by_stage.get(stage)
            if hint and hint.get("hint_text"):
                properties[prop_name] = {
                    "rich_text": [{"text": {"content": hint["hint_text"][:2000]}}]
                }

        # 기존 페이지 확인 (upsert)
        existing_page_id = problem.get("notion_page_id")
        if not existing_page_id:
            existing = self._find_page_by_problem_id(problem_id)
            if existing:
                existing_page_id = existing["id"]

        if existing_page_id:
            # 기존 페이지 업데이트
            try:
                page = self.client.pages.update(
                    page_id=existing_page_id, properties=properties
                )
                self._clear_page_blocks(existing_page_id)
                self._append_review_content(existing_page_id, problem, hints)
            except Exception:
                # 페이지가 삭제된 경우 새로 생성
                page = self._create_review_page_new(properties, problem, hints)
        else:
            page = self._create_review_page_new(properties, problem, hints)

        return page

    def _create_review_page_new(self, properties: dict, problem: dict, hints: list) -> dict:
        """새 검수 페이지 생성"""
        page = self.client.pages.create(
            parent={"database_id": self.database_id},
            properties=properties,
        )
        self._append_review_content(page["id"], problem, hints)
        return page

    def _find_page_by_problem_id(self, problem_id: str) -> Optional[dict]:
        """Notion DB에서 문제 ID로 기존 페이지 검색"""
        query_body = {
            "filter": {
                "property": "문제 ID",
                "title": {"equals": problem_id}
            }
        }
        response = self.client.request(
            path=f"databases/{self.database_id}/query",
            method="POST",
            body=query_body,
        )
        results = response.get("results", [])
        return results[0] if results else None

    def _clear_page_blocks(self, page_id: str):
        """페이지의 모든 블록 삭제"""
        response = self._api_call_with_retry(
            self.client.blocks.children.list, block_id=page_id
        )
        for block in response.get("results", []):
            try:
                self._api_call_with_retry(
                    self.client.blocks.delete, block_id=block["id"]
                )
            except Exception as e:
                print(f"  블록 삭제 실패 ({block['id'][:8]}): {e}")

    def _append_review_content(self, page_id: str, problem: dict, hints: list):
        """검수 페이지 본문 블록 추가 (2단계: 상위 블록 → 토글 자식)"""
        all_blocks = self._build_review_blocks(problem, hints)

        # 토글 자식 블록 분리
        top_blocks = []
        toggle_children = {}  # index -> children list

        for i, block in enumerate(all_blocks):
            children = block.pop("_children", None)
            top_blocks.append(block)
            if children:
                toggle_children[i] = children

        # 100개 단위로 배치 추가
        for batch_start in range(0, len(top_blocks), 100):
            batch = top_blocks[batch_start:batch_start + 100]
            response = self._api_call_with_retry(
                self.client.blocks.children.append,
                block_id=page_id, children=batch
            )

            # 토글 블록에 자식 추가
            results = response.get("results", [])
            for j, result_block in enumerate(results):
                orig_idx = batch_start + j
                if orig_idx in toggle_children:
                    self._api_call_with_retry(
                        self.client.blocks.children.append,
                        block_id=result_block["id"],
                        children=toggle_children[orig_idx],
                    )

    def _build_review_blocks(self, problem: dict, hints: list) -> list:
        """검수 페이지 본문 블록 리스트 구성"""
        blocks = []

        # --- 📋 문제 정보 ---
        blocks.append(self._heading2("📋 문제 정보"))

        answer_type_kr = "객관식" if problem.get("answer_type") == "multiple" else "주관식"
        info = (
            f"과목: {problem.get('subject') or '미정'}\n"
            f"단원: {problem.get('unit') or '미정'}\n"
            f"배점: {problem.get('score') or '?'}점\n"
            f"유형: {answer_type_kr}\n"
            f"정답: {problem.get('answer') or '?'}"
        )
        blocks.append(self._callout(info, emoji="📋"))

        # --- 🖼️ 문제 이미지 ---
        blocks.append(self._divider())
        blocks.append(self._heading2("🖼️ 문제 이미지"))

        image_url = problem.get("problem_image_url")
        if image_url:
            blocks.append({
                "object": "block",
                "type": "image",
                "image": {"type": "external", "external": {"url": image_url}},
            })
        else:
            blocks.append(self._callout("이미지 없음 - 업로드 필요", emoji="⚠️", color="yellow_background"))

        # --- 📝 풀이 (토글, 힌트보다 먼저) ---
        blocks.append(self._divider())

        solution = problem.get("solution") or ""
        if solution:
            solution_children = self._split_text_to_blocks(solution)
        else:
            solution_children = [self._callout("풀이 미입력", emoji="⚠️", color="yellow_background")]

        blocks.append(self._toggle_heading("📝 풀이", children=solution_children))

        # --- 힌트 (토글) ---
        blocks.append(self._divider())

        hint_config = {
            1: ("💡 힌트 1단계: 개념 방향", "💡", "blue_background"),
            2: ("🔑 힌트 2단계: 핵심 전환", "🔑", "yellow_background"),
            3: ("🎯 힌트 3단계: 결정적 한 줄", "🎯", "red_background"),
        }
        hints_by_stage = {h["stage"]: h for h in hints}

        for stage in [1, 2, 3]:
            label, emoji, color = hint_config[stage]
            hint = hints_by_stage.get(stage)
            if hint and hint.get("hint_text"):
                hint_content = [self._callout(hint["hint_text"], emoji=emoji, color=color)]
            else:
                hint_content = [self._callout("힌트 미입력", emoji="⚠️", color="yellow_background")]
            blocks.append(self._toggle_heading(label, children=hint_content))

        # --- 📌 출제 의도 (토글) ---
        blocks.append(self._divider())

        intent_parts = []
        if problem.get("intent_1"):
            intent_parts.append(self._paragraph(problem["intent_1"]))
        if problem.get("intent_2"):
            intent_parts.append(self._paragraph(problem["intent_2"]))
        if not intent_parts:
            intent_parts = [self._callout("출제 의도 미입력", emoji="⚠️", color="yellow_background")]
        blocks.append(self._toggle_heading("📌 출제 의도", children=intent_parts))

        # --- ✅ 검수 체크리스트 ---
        blocks.append(self._callout("검수 체크리스트", emoji="✅"))

        checklist_items = [
            "문제 이미지 확인",
            "정답 확인",
            "배점 확인",
            "정답 유형(객관식/주관식) 확인",
            "풀이 정확성 확인",
            "힌트 3단계 확인",
            "과목/단원 분류 확인",
            "난이도 설정 (1~5)",
        ]
        for item in checklist_items:
            blocks.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"type": "text", "text": {"content": item}}],
                    "checked": False,
                },
            })

        return blocks

    def _split_text_to_blocks(self, text: str, max_len: int = 1900) -> list:
        """긴 텍스트를 2000자 제한에 맞게 여러 paragraph 블록으로 분할"""
        lines = text.split("\n")
        blocks = []
        chunk_lines = []
        chunk_len = 0

        for line in lines:
            line_len = len(line) + 1
            if chunk_len + line_len > max_len and chunk_lines:
                blocks.append(self._paragraph("\n".join(chunk_lines)))
                chunk_lines = []
                chunk_len = 0
            chunk_lines.append(line)
            chunk_len += line_len

        if chunk_lines:
            blocks.append(self._paragraph("\n".join(chunk_lines)))

        return blocks

    # --- 블록 빌더 헬퍼 ---

    @staticmethod
    def _divider():
        return {"object": "block", "type": "divider", "divider": {}}

    @staticmethod
    def _heading2(text):
        return {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
            },
        }

    @staticmethod
    def _paragraph(text):
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
            },
        }

    @staticmethod
    def _callout(text, emoji="💡", color="default"):
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
                "icon": {"type": "emoji", "emoji": emoji},
                "color": color,
            },
        }

    @staticmethod
    def _toggle_heading(text, children=None):
        block = {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
                "is_toggleable": True,
            },
        }
        block["_children"] = children or []
        return block

    # ============================================
    # Notion → Supabase 동기화
    # ============================================

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
                problem_id = data.get("문제 ID") if "data" in dir() else page.get("id", "unknown")
                print(f"동기화 실패: {problem_id} - {e}")

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
