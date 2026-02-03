"""
Designer 에이전트 - 디자인 담당
카카오 템플릿, 문제 이미지, UI 설계
"""

from typing import Optional, Dict, List, Any
from .base import BaseAgent, Task, TaskStatus, AgentMessage


class DesignerAgent(BaseAgent):
    """
    디자인 에이전트

    역할:
    - 카카오톡 메시지 템플릿 디자인
    - 문제 이미지 레이아웃 설계
    - UI/UX 설계
    - 브랜딩 및 시각 요소 관리
    """

    def __init__(self):
        super().__init__(
            name="designer",
            role="디자인",
            capabilities=[
                "카카오톡 템플릿 디자인",
                "문제 이미지 레이아웃",
                "UI/UX 설계",
                "브랜딩",
                "아이콘/그래픽 디자인",
                "반응형 디자인",
            ]
        )
        self.templates: Dict[str, Dict] = {}
        self.design_specs: Dict[str, Dict] = {}

    def create_kakao_template(self, template_type: str) -> Dict[str, Any]:
        """카카오톡 메시지 템플릿 생성"""
        self.log(f"카카오톡 템플릿 생성: {template_type}")

        templates = {
            "daily_problem": {
                "name": "오늘의 문제",
                "type": "feed",
                "content": {
                    "title": "[오늘의 수학문제]",
                    "description": "#{year}학년도 #{exam_type} #{question_no}번\n배점: #{score}점 | 단원: #{unit}",
                    "image_url": "#{problem_image_url}",
                    "link": {
                        "web_url": "#{web_url}",
                        "mobile_url": "#{mobile_url}",
                    },
                },
                "buttons": [
                    {"type": "web", "label": "문제 풀기", "url": "#{solve_url}"},
                    {"type": "web", "label": "힌트 보기", "url": "#{hint_url}"},
                ],
            },
            "hint": {
                "name": "힌트 제공",
                "type": "text",
                "content": {
                    "text": "💡 힌트 #{stage}\n\n#{hint_text}\n\n---\n⏰ 다음 힌트: #{next_hint_time}",
                },
                "buttons": [
                    {"type": "web", "label": "다음 힌트", "url": "#{next_hint_url}"},
                    {"type": "web", "label": "정답 제출", "url": "#{submit_url}"},
                ],
            },
            "answer_result": {
                "name": "정답 결과",
                "type": "feed",
                "content": {
                    "title": "#{result_emoji} #{result_text}",
                    "description": "정답: #{correct_answer}\n풀이 시간: #{time_spent}\n#{feedback}",
                    "image_url": "#{solution_image_url}",
                },
                "buttons": [
                    {"type": "web", "label": "풀이 보기", "url": "#{solution_url}"},
                    {"type": "web", "label": "오답노트 저장", "url": "#{save_url}"},
                ],
            },
            "weekly_report": {
                "name": "주간 리포트",
                "type": "feed",
                "content": {
                    "title": "📊 이번 주 학습 리포트",
                    "description": "풀이 문제: #{total_solved}개\n정답률: #{correct_rate}%\n취약 단원: #{weak_unit}",
                    "image_url": "#{chart_image_url}",
                },
                "buttons": [
                    {"type": "web", "label": "상세 보기", "url": "#{report_url}"},
                ],
            },
        }

        template = templates.get(template_type, templates["daily_problem"])
        self.templates[template_type] = template
        return template

    def design_problem_image_layout(self) -> Dict[str, Any]:
        """문제 이미지 레이아웃 설계"""
        self.log("문제 이미지 레이아웃 설계")

        layout = {
            "name": "problem_card",
            "dimensions": {
                "width": 800,
                "height": "auto",
                "max_height": 1200,
                "padding": 40,
            },
            "components": [
                {
                    "type": "header",
                    "height": 60,
                    "elements": [
                        {"type": "text", "content": "#{year} #{exam_type}", "style": "year_badge"},
                        {"type": "text", "content": "#{question_no}번", "style": "question_no"},
                        {"type": "badge", "content": "#{score}점", "style": "score_badge"},
                    ],
                },
                {
                    "type": "problem_area",
                    "min_height": 300,
                    "elements": [
                        {"type": "image", "src": "#{problem_image}", "fit": "contain"},
                    ],
                },
                {
                    "type": "footer",
                    "height": 50,
                    "elements": [
                        {"type": "text", "content": "단원: #{unit}", "style": "unit_label"},
                        {"type": "logo", "src": "assets/logo.png", "size": 30},
                    ],
                },
            ],
            "styles": {
                "background": "#FFFFFF",
                "border_radius": 16,
                "shadow": "0 4px 12px rgba(0,0,0,0.1)",
                "year_badge": {
                    "font_size": 14,
                    "color": "#666666",
                    "background": "#F0F0F0",
                    "padding": "4px 12px",
                    "border_radius": 12,
                },
                "question_no": {
                    "font_size": 24,
                    "font_weight": "bold",
                    "color": "#333333",
                },
                "score_badge": {
                    "font_size": 14,
                    "color": "#FFFFFF",
                    "background": "#4A90D9",
                    "padding": "4px 12px",
                    "border_radius": 12,
                },
                "unit_label": {
                    "font_size": 12,
                    "color": "#888888",
                },
            },
        }

        self.design_specs["problem_image_layout"] = layout
        return layout

    def design_web_ui(self) -> Dict[str, Any]:
        """웹 UI 설계"""
        self.log("웹 UI 설계")

        ui_spec = {
            "design_system": {
                "colors": {
                    "primary": "#4A90D9",
                    "secondary": "#7B68EE",
                    "success": "#28A745",
                    "warning": "#FFC107",
                    "error": "#DC3545",
                    "background": "#F5F7FA",
                    "surface": "#FFFFFF",
                    "text_primary": "#333333",
                    "text_secondary": "#666666",
                },
                "typography": {
                    "font_family": "'Pretendard', -apple-system, sans-serif",
                    "h1": {"size": 32, "weight": 700},
                    "h2": {"size": 24, "weight": 600},
                    "h3": {"size": 18, "weight": 600},
                    "body": {"size": 16, "weight": 400},
                    "caption": {"size": 14, "weight": 400},
                },
                "spacing": {
                    "xs": 4,
                    "sm": 8,
                    "md": 16,
                    "lg": 24,
                    "xl": 32,
                },
                "border_radius": {
                    "sm": 4,
                    "md": 8,
                    "lg": 16,
                    "full": 9999,
                },
            },
            "pages": {
                "home": {
                    "sections": ["hero", "today_problem", "stats", "cta"],
                },
                "solve": {
                    "sections": ["problem_display", "answer_input", "hint_panel", "timer"],
                },
                "dashboard": {
                    "sections": ["overview", "progress_chart", "weak_units", "history"],
                },
                "pricing": {
                    "sections": ["plans", "features", "faq", "cta"],
                },
            },
            "components": [
                "Button",
                "Card",
                "Modal",
                "Input",
                "Select",
                "Timer",
                "ProgressBar",
                "Chart",
                "Badge",
                "Toast",
            ],
        }

        self.design_specs["web_ui"] = ui_spec
        return ui_spec

    def design_mobile_responsive(self) -> Dict[str, Any]:
        """모바일 반응형 설계"""
        self.log("모바일 반응형 설계")

        responsive = {
            "breakpoints": {
                "mobile": "max-width: 480px",
                "tablet": "max-width: 768px",
                "desktop": "min-width: 769px",
            },
            "mobile_adaptations": {
                "problem_card": {
                    "width": "100%",
                    "padding": 20,
                    "font_scale": 0.9,
                },
                "navigation": {
                    "type": "bottom_tab",
                    "items": ["홈", "문제", "통계", "설정"],
                },
                "buttons": {
                    "full_width": True,
                    "height": 48,
                },
            },
            "touch_targets": {
                "min_size": 44,
                "spacing": 8,
            },
        }

        self.design_specs["responsive"] = responsive
        return responsive

    def create_branding_assets(self) -> Dict[str, Any]:
        """브랜딩 에셋 생성"""
        self.log("브랜딩 에셋 생성")

        branding = {
            "logo": {
                "primary": "assets/logo_primary.svg",
                "white": "assets/logo_white.svg",
                "icon": "assets/logo_icon.svg",
            },
            "app_name": "수학배달",
            "tagline": "매일 한 문제, 수능 수학 완성",
            "social": {
                "og_image": "assets/og_image.png",
                "favicon": "assets/favicon.ico",
            },
            "kakao_profile": {
                "image": "assets/kakao_profile.png",
                "background": "assets/kakao_bg.png",
            },
        }

        self.design_specs["branding"] = branding
        return branding

    def process_task(self, task: Task) -> Any:
        """작업 처리"""
        self.log(f"작업 처리: {task.title}")
        task.status = TaskStatus.IN_PROGRESS

        title_lower = task.title.lower()

        try:
            if "템플릿" in task.title or "template" in title_lower:
                template_type = task.metadata.get("template_type", "daily_problem")
                result = self.create_kakao_template(template_type)
                task.update_status(TaskStatus.COMPLETED, result=result)
                return result

            if "레이아웃" in task.title or "layout" in title_lower:
                result = self.design_problem_image_layout()
                task.update_status(TaskStatus.COMPLETED, result=result)
                return result

            if "ui" in title_lower or "웹" in task.title:
                result = self.design_web_ui()
                task.update_status(TaskStatus.COMPLETED, result=result)
                return result

            if "반응형" in task.title or "모바일" in task.title:
                result = self.design_mobile_responsive()
                task.update_status(TaskStatus.COMPLETED, result=result)
                return result

            if "브랜딩" in task.title or "로고" in task.title:
                result = self.create_branding_assets()
                task.update_status(TaskStatus.COMPLETED, result=result)
                return result

            # 기본 처리
            result = {"status": "processed", "task": task.title}
            task.update_status(TaskStatus.COMPLETED, result=result)
            return result

        except Exception as e:
            task.update_status(TaskStatus.FAILED, error=str(e))
            return {"error": str(e)}

    def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """메시지 처리"""
        self.log(f"메시지 처리: {message.message_type}")

        if message.message_type == "template_request":
            template_type = message.content.get("type", "daily_problem")
            template = self.create_kakao_template(template_type)
            return self.send_message(
                message.sender,
                "template_response",
                {"template": template}
            )

        if message.message_type == "design_review_request":
            return self.send_message(
                message.sender,
                "design_review_response",
                {
                    "status": "reviewed",
                    "feedback": "디자인 검토 완료",
                    "specs": self.design_specs,
                }
            )

        return None

    def get_all_templates(self) -> Dict[str, Dict]:
        """모든 템플릿 조회"""
        # 기본 템플릿들 생성
        template_types = ["daily_problem", "hint", "answer_result", "weekly_report"]
        for t in template_types:
            if t not in self.templates:
                self.create_kakao_template(t)
        return self.templates

    def get_design_specs(self) -> Dict[str, Dict]:
        """모든 디자인 스펙 조회"""
        return self.design_specs
