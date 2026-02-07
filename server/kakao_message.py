"""
Kakao Talk Message Service
Sends math problems to users via KakaoTalk
"""

import os
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class KakaoMessageService:
    """Send messages via KakaoTalk API"""

    SEND_ME_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"

    def __init__(self):
        pass

    def send_text_to_me(self, access_token: str, text: str, button_title: str = None, button_url: str = None) -> Dict[str, Any]:
        """
        Send text message to user (나에게 보내기)

        Args:
            access_token: User's Kakao access token
            text: Message text
            button_title: Optional button text
            button_url: Optional button URL

        Returns:
            API response dict
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        template = {
            "object_type": "text",
            "text": text,
            "link": {
                "web_url": "https://kice.re.kr",
                "mobile_web_url": "https://kice.re.kr"
            }
        }

        # Add button if provided (allow localhost for dev)
        if button_title and button_url:
            template["link"]["web_url"] = button_url
            template["link"]["mobile_web_url"] = button_url
            template["button_title"] = button_title

        import json
        data = {
            "template_object": json.dumps(template)
        }

        try:
            response = requests.post(
                self.SEND_ME_URL,
                headers=headers,
                data=data,
                timeout=10
            )

            if response.status_code == 200:
                return {"success": True, "result": response.json()}
            else:
                return {
                    "success": False,
                    "error": response.json(),
                    "status_code": response.status_code
                }

        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    def send_feed_with_image(
        self,
        access_token: str,
        title: str,
        description: str,
        image_url: str,
        button_title: str = None,
        button_url: str = None
    ) -> Dict[str, Any]:
        """
        Send list message with image (이미지가 포함된 리스트 메시지)

        Args:
            access_token: User's Kakao access token
            title: Feed title
            description: Feed description
            image_url: Image URL (must be publicly accessible)
            button_title: Button text
            button_url: Button URL

        Returns:
            API response dict
        """
        import json

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # Feed template with minimal config
        # Use button_url for both content link and button link (clicking anywhere opens the problem)
        default_url = button_url if button_url else "https://kice.re.kr"

        template = {
            "object_type": "feed",
            "content": {
                "title": title,
                "description": description,
                "image_url": image_url,
                "link": {
                    "web_url": default_url,
                    "mobile_web_url": default_url
                }
            }
        }

        # Add button if provided (allow localhost for dev)
        if button_title and button_url:
            print(f"[Kakao Button Debug] Adding button with URL: {button_url}")
            template["buttons"] = [{
                "title": button_title,
                "link": {
                    "web_url": button_url,
                    "mobile_web_url": button_url
                }
            }]
        else:
            print(f"[Kakao Button Debug] No button added (missing title or url)")

        data = {
            "template_object": json.dumps(template)
        }
        # Use ensure_ascii=True to avoid cp949 encoding errors with emojis
        print(f"[Kakao Template Debug] Template length: {len(json.dumps(template))} chars, has buttons: {'buttons' in template}")

        try:
            response = requests.post(
                self.SEND_ME_URL,
                headers=headers,
                data=data,
                timeout=10
            )

            if response.status_code == 200:
                return {"success": True, "result": response.json()}
            else:
                return {
                    "success": False,
                    "error": response.json(),
                    "status_code": response.status_code
                }

        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    def send_math_problem(
        self,
        access_token: str,
        problem_id: str,
        problem_text: str,
        problem_image_url: str = None,
        year: int = None,
        exam: str = None,
        number: int = None,
        difficulty: str = None,
        unit: str = None,
        button_title: str = None,
        button_url: str = None
    ) -> Dict[str, Any]:
        """
        Send math problem to user (이미지 우선, 없으면 텍스트)

        Args:
            access_token: User's Kakao access token
            problem_id: Problem ID
            problem_text: Problem description
            problem_image_url: URL to problem image
            year: Exam year
            exam: Exam type (수능, 6월, 9월)
            number: Problem number
            difficulty: Problem difficulty (2점, 3점, 4점)
            unit: Problem unit/category
            button_title: Optional button text
            button_url: Optional button URL (problem viewer)

        Returns:
            API response dict
        """
        # Build title with clean format
        exam_emoji = {
            "CSAT": "🎓",
            "KICE6": "📘",
            "KICE9": "📙"
        }.get(exam, "📝")

        exam_name = {
            "CSAT": "수능",
            "KICE6": "6월 평가원",
            "KICE9": "9월 평가원"
        }.get(exam, exam or "")

        title = f"{exam_emoji} {year or ''} {exam_name} {number or ''}번".strip()
        if not title or not exam_name:
            title = f"📐 수학 문제"

        # Build description with elegant layout
        desc_parts = []

        # Metadata line (difficulty + unit)
        if difficulty or unit:
            metadata = []
            if difficulty:
                diff_emoji = {"2점": "⭐", "3점": "⭐⭐", "4점": "⭐⭐⭐"}.get(difficulty, "⭐⭐")
                metadata.append(f"{diff_emoji} {difficulty}")
            if unit:
                metadata.append(f"📚 {unit}")
            desc_parts.append(" · ".join(metadata))

        # Clean call to action
        desc_parts.append("\n💡 버튼을 눌러 문제를 풀어보세요!")

        desc = "\n".join(desc_parts)

        # Send as feed with image (card format)
        if problem_image_url:
            # Add timestamp to bypass Kakao CDN cache
            import time
            cache_buster = f"?t={int(time.time())}"
            image_url_with_cache_buster = problem_image_url + cache_buster

            return self.send_feed_with_image(
                access_token=access_token,
                title=title,
                description=desc,
                image_url=image_url_with_cache_buster,
                button_title=button_title,
                button_url=button_url
            )

        # Fallback to text message without image
        message = f"[{title}]\n\n{problem_text}\n\n{desc}"

        return self.send_text_to_me(
            access_token=access_token,
            text=message
        )

    def send_hint(
        self,
        access_token: str,
        hint_level: int,
        hint_text: str
    ) -> Dict[str, Any]:
        """
        Send hint to user

        Args:
            access_token: User's Kakao access token
            hint_level: Hint level (1, 2, or 3)
            hint_text: Hint content

        Returns:
            API response dict
        """
        message = f"[힌트 {hint_level}단계]\n\n{hint_text}"

        if hint_level < 3:
            message += f"\n\n다음 힌트가 필요하면 '힌트'라고 답해주세요."

        return self.send_text_to_me(
            access_token=access_token,
            text=message
        )

    def send_answer(
        self,
        access_token: str,
        answer: str,
        solution: str,
        is_correct: bool = None
    ) -> Dict[str, Any]:
        """
        Send answer and solution to user

        Args:
            access_token: User's Kakao access token
            answer: Correct answer
            solution: Solution explanation
            is_correct: Whether user's answer was correct

        Returns:
            API response dict
        """
        if is_correct is True:
            header = "정답입니다!\n\n"
        elif is_correct is False:
            header = "아쉽네요. 정답이 아닙니다.\n\n"
        else:
            header = ""

        message = f"{header}[정답] {answer}\n\n[풀이]\n{solution}\n\n다음 문제를 원하시면 '다음'이라고 답해주세요."

        return self.send_text_to_me(
            access_token=access_token,
            text=message
        )


# Test
if __name__ == "__main__":
    print("Kakao Message Service")
    print("Use with user's access_token after login")
