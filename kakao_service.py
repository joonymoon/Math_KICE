"""
카카오톡 메시지 발송 서비스

필요한 가입:
1. 카카오 개발자 (https://developers.kakao.com)
2. 카카오톡 채널 (https://center-pf.kakao.com)
3. (선택) 알림톡 발송 대행사 (NHN Cloud, 카카오 i 커넥트 등)
"""

import os
import re
import io
import base64
import requests
from typing import Optional, Tuple
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()


# ============================================
# 수학 기호 변환 유틸리티
# ============================================

class MathFormatter:
    """수학 표기를 카카오톡에서 보기 좋게 변환"""

    # 위첨자 변환 테이블
    SUPERSCRIPT = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
        '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾',
        'n': 'ⁿ', 'x': 'ˣ', 'y': 'ʸ', 'a': 'ᵃ', 'b': 'ᵇ',
        'c': 'ᶜ', 'd': 'ᵈ', 'e': 'ᵉ', 'f': 'ᶠ', 'g': 'ᵍ',
        'h': 'ʰ', 'i': 'ⁱ', 'j': 'ʲ', 'k': 'ᵏ', 'l': 'ˡ',
        'm': 'ᵐ', 'o': 'ᵒ', 'p': 'ᵖ', 'r': 'ʳ', 's': 'ˢ',
        't': 'ᵗ', 'u': 'ᵘ', 'v': 'ᵛ', 'w': 'ʷ', 'z': 'ᶻ',
    }

    # 아래첨자 변환 테이블
    SUBSCRIPT = {
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
        '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
        '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎',
        'a': 'ₐ', 'e': 'ₑ', 'h': 'ₕ', 'i': 'ᵢ', 'j': 'ⱼ',
        'k': 'ₖ', 'l': 'ₗ', 'm': 'ₘ', 'n': 'ₙ', 'o': 'ₒ',
        'p': 'ₚ', 'r': 'ᵣ', 's': 'ₛ', 't': 'ₜ', 'u': 'ᵤ',
        'v': 'ᵥ', 'x': 'ₓ',
    }

    @classmethod
    def to_superscript(cls, text: str) -> str:
        """텍스트를 위첨자로 변환"""
        return ''.join(cls.SUPERSCRIPT.get(c, c) for c in text)

    @classmethod
    def to_subscript(cls, text: str) -> str:
        """텍스트를 아래첨자로 변환"""
        return ''.join(cls.SUBSCRIPT.get(c, c) for c in text)

    @classmethod
    def format_math(cls, text: str) -> str:
        """
        수학 표기를 카카오톡 친화적으로 변환

        변환 규칙:
        - 2^x → 2ˣ
        - x^2 → x²
        - a_n → aₙ
        - lim(x→a) → lim[x→a]
        - sqrt → √
        """
        if not text:
            return text

        result = text

        # 1. 거듭제곱 변환: ^{...} 또는 ^문자
        # 예: x^{2n+1} → x²ⁿ⁺¹, 2^x → 2ˣ
        def replace_power(match):
            base = match.group(1) if match.group(1) else ''
            exp = match.group(2)
            # 중괄호 제거
            exp = exp.strip('{}')
            return base + cls.to_superscript(exp)

        # ^{...} 형태
        result = re.sub(r'(\w?)\^\{([^}]+)\}', replace_power, result)
        # ^단일문자 형태 (이미 위첨자가 아닌 경우)
        result = re.sub(r'(\w)\^([0-9a-zA-Z])', replace_power, result)

        # 2. 아래첨자 변환: _{...} 또는 _문자
        # 예: a_{n+1} → aₙ₊₁, a_n → aₙ
        def replace_subscript(match):
            base = match.group(1) if match.group(1) else ''
            sub = match.group(2)
            sub = sub.strip('{}')
            return base + cls.to_subscript(sub)

        # _{...} 형태
        result = re.sub(r'(\w?)_\{([^}]+)\}', replace_subscript, result)
        # _단일문자 형태
        result = re.sub(r'(\w)_([0-9a-zA-Z])', replace_subscript, result)

        # 3. 특수 표기 변환
        replacements = {
            'sqrt': '√',
            '\\sqrt': '√',
            '\\times': '×',
            '\\div': '÷',
            '\\pm': '±',
            '\\infty': '∞',
            '\\pi': 'π',
            '\\theta': 'θ',
            '\\alpha': 'α',
            '\\beta': 'β',
            '\\gamma': 'γ',
            '\\delta': 'δ',
            '\\epsilon': 'ε',
            '\\lambda': 'λ',
            '\\sigma': 'σ',
            '\\sum': 'Σ',
            '\\prod': 'Π',
            '\\int': '∫',
            '\\partial': '∂',
            '\\neq': '≠',
            '\\leq': '≤',
            '\\geq': '≥',
            '\\approx': '≈',
            '\\equiv': '≡',
            '\\cdot': '·',
            '\\ldots': '…',
            '->': '→',
            '<-': '←',
            '<->': '↔',
            '<=': '≤',
            '>=': '≥',
            '!=': '≠',
            '*': '×',
        }

        for old, new in replacements.items():
            result = result.replace(old, new)

        # 4. lim 표기 정리
        # lim(x→a) 형태는 유지 (가독성)
        # 또는 lim 아래첨자로: lim_{x→a} → lim 형태 유지

        # 5. 분수 표기 (간단한 형태만)
        # \frac{a}{b} → a/b (카톡에서 분수 표현 제한적)
        result = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', result)

        return result

    @classmethod
    def format_solution(cls, solution: str) -> str:
        """풀이 텍스트를 카카오톡용으로 포맷팅"""
        if not solution:
            return solution

        # 수학 기호 변환
        formatted = cls.format_math(solution)

        # 줄바꿈 정리 (연속 줄바꿈은 2개까지만)
        formatted = re.sub(r'\n{3,}', '\n\n', formatted)

        return formatted

    @classmethod
    def format_hint(cls, hint: str) -> str:
        """힌트 텍스트를 카카오톡용으로 포맷팅"""
        return cls.format_math(hint) if hint else hint

    @classmethod
    def has_complex_math(cls, text: str) -> bool:
        """복잡한 수식이 포함되어 있는지 확인"""
        complex_patterns = [
            r'\\frac\{',        # 분수
            r'\\sqrt\{',        # 제곱근 (중괄호 포함)
            r'\\sum_',          # 시그마
            r'\\int_',          # 정적분
            r'\\lim_',          # 극한 (아래첨자)
            r'\\prod_',         # 곱기호
            r'\\begin\{',       # 행렬, 정렬 등
            r'\\matrix',        # 행렬
            r'\\binom',         # 이항계수
            r'\\overset',       # 위에 기호
            r'\\underset',      # 아래에 기호
        ]
        for pattern in complex_patterns:
            if re.search(pattern, text):
                return True
        return False


# ============================================
# 수식 이미지 생성기
# ============================================

class MathImageGenerator:
    """
    LaTeX 수식을 이미지로 변환하는 클래스

    여러 무료 API를 지원:
    1. CodeCogs (추천) - 안정적, 무료
    2. QuickLaTeX - 고품질
    3. i.upmath.me - 간단한 수식용
    """

    # 이미지 생성 서비스 설정
    CODECOGS_URL = "https://latex.codecogs.com/png.latex"
    QUICKLATEX_URL = "https://quicklatex.com/latex3.f"
    UPMATH_URL = "https://i.upmath.me/svg"

    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """
        Args:
            supabase_url: Supabase 프로젝트 URL (이미지 저장용)
            supabase_key: Supabase anon key
        """
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")

    def latex_to_image_url(self, latex: str, method: str = "codecogs") -> str:
        """
        LaTeX 수식을 이미지 URL로 변환

        Args:
            latex: LaTeX 수식 문자열
            method: 사용할 서비스 (codecogs, quicklatex, upmath)

        Returns:
            이미지 URL
        """
        # LaTeX 이스케이프 처리
        latex = latex.strip()

        if method == "codecogs":
            return self._codecogs_url(latex)
        elif method == "quicklatex":
            return self._quicklatex_url(latex)
        elif method == "upmath":
            return self._upmath_url(latex)
        else:
            return self._codecogs_url(latex)

    def _codecogs_url(self, latex: str) -> str:
        """CodeCogs API로 이미지 URL 생성"""
        # URL 인코딩
        encoded = quote(latex)
        # 배경색 흰색, 글자색 검정, 크기 조절
        return f"{self.CODECOGS_URL}?\\dpi{{150}}\\bg_white {encoded}"

    def _quicklatex_url(self, latex: str) -> str:
        """QuickLaTeX API로 이미지 URL 생성"""
        # QuickLaTeX는 POST 요청으로 이미지 URL 반환
        data = {
            "formula": latex,
            "fsize": "17px",
            "fcolor": "000000",
            "mode": "0",
            "out": "1",
            "remhost": "quicklatex.com"
        }
        try:
            response = requests.post(self.QUICKLATEX_URL, data=data, timeout=10)
            if response.status_code == 200:
                # 응답에서 이미지 URL 추출
                lines = response.text.split('\n')
                if lines and lines[0].startswith('0'):
                    parts = lines[0].split(' ')
                    if len(parts) >= 2:
                        return parts[1]
        except Exception:
            pass
        # 실패 시 CodeCogs로 폴백
        return self._codecogs_url(latex)

    def _upmath_url(self, latex: str) -> str:
        """Upmath API로 SVG URL 생성"""
        encoded = quote(latex)
        return f"{self.UPMATH_URL}/{encoded}"

    def generate_solution_image(self, solution_latex: str) -> str:
        """
        풀이 전체를 이미지로 생성

        긴 풀이는 여러 이미지로 분할 가능
        """
        return self.latex_to_image_url(solution_latex)

    def generate_formula_image(self, formula: str) -> str:
        """단일 수식 이미지 생성"""
        return self.latex_to_image_url(formula)

    def upload_to_supabase(self, image_url: str, filename: str) -> Optional[str]:
        """
        외부 이미지를 Supabase Storage에 업로드

        Returns:
            Supabase에 저장된 이미지의 공개 URL
        """
        if not self.supabase_url or not self.supabase_key:
            return image_url  # Supabase 미설정 시 원본 URL 반환

        try:
            # 이미지 다운로드
            response = requests.get(image_url, timeout=10)
            if response.status_code != 200:
                return image_url

            image_data = response.content

            # Supabase Storage에 업로드
            upload_url = f"{self.supabase_url}/storage/v1/object/math-images/{filename}"
            headers = {
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "image/png"
            }

            upload_response = requests.post(
                upload_url,
                headers=headers,
                data=image_data,
                timeout=30
            )

            if upload_response.status_code in [200, 201]:
                # 공개 URL 반환
                return f"{self.supabase_url}/storage/v1/object/public/math-images/{filename}"

        except Exception:
            pass

        return image_url  # 실패 시 원본 URL 반환


# ============================================
# 풀이/힌트 LaTeX 변환기
# ============================================

class SolutionToLatex:
    """텍스트 풀이를 LaTeX 형식으로 변환"""

    @staticmethod
    def convert(text: str) -> str:
        """
        일반 텍스트 수식을 LaTeX로 변환

        예시:
        - x^2 → x^{2}
        - sqrt(x) → \\sqrt{x}
        - a/b → \\frac{a}{b}
        """
        result = text

        # 제곱근
        result = re.sub(r'sqrt\(([^)]+)\)', r'\\sqrt{\1}', result)
        result = re.sub(r'√\(([^)]+)\)', r'\\sqrt{\1}', result)
        result = re.sub(r'√(\w)', r'\\sqrt{\1}', result)

        # 분수 (a/b 형태를 \frac{a}{b}로)
        # 단, 이미 분수가 아닌 경우만 (예: 1/2, x/y)
        result = re.sub(r'(\w+)/(\w+)', r'\\frac{\1}{\2}', result)

        # 지수를 중괄호로
        result = re.sub(r'\^(\d+)', r'^{\1}', result)
        result = re.sub(r'\^([a-zA-Z])', r'^{\1}', result)

        # 아래첨자를 중괄호로
        result = re.sub(r'_(\d+)', r'_{\1}', result)
        result = re.sub(r'_([a-zA-Z])', r'_{\1}', result)

        # 특수 기호
        replacements = {
            '×': '\\times ',
            '÷': '\\div ',
            '±': '\\pm ',
            '∞': '\\infty ',
            'π': '\\pi ',
            '→': '\\rightarrow ',
            '≤': '\\leq ',
            '≥': '\\geq ',
            '≠': '\\neq ',
            '∫': '\\int ',
            'Σ': '\\sum ',
            '∴': '\\therefore ',
        }

        for old, new in replacements.items():
            result = result.replace(old, new)

        return result

    @staticmethod
    def wrap_display_math(latex: str) -> str:
        """디스플레이 수식으로 감싸기"""
        return f"$${latex}$$"

    @staticmethod
    def wrap_inline_math(latex: str) -> str:
        """인라인 수식으로 감싸기"""
        return f"${latex}$"


class KakaoMessageService:
    """카카오톡 메시지 발송 서비스"""

    def __init__(self):
        # 카카오 REST API 키
        self.rest_api_key = os.getenv("KAKAO_REST_API_KEY")
        # 사용자 액세스 토큰 (로그인 후 발급)
        self.access_token = os.getenv("KAKAO_ACCESS_TOKEN")
        # 카카오톡 채널 ID (알림톡용)
        self.channel_id = os.getenv("KAKAO_CHANNEL_ID")

        self.base_url = "https://kapi.kakao.com"

    # ============================================
    # 방법 1: 나에게 보내기 (테스트용)
    # ============================================

    def send_to_me(self, problem: dict) -> dict:
        """
        나에게 보내기 (테스트용)
        - 카카오 로그인한 본인에게만 발송 가능
        - 개발/테스트 단계에서 사용
        """
        url = f"{self.base_url}/v2/api/talk/memo/default/send"

        # 메시지 템플릿 구성
        template = self._build_problem_template(problem)

        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={"template_object": template}
        )

        return response.json()

    # ============================================
    # 방법 2: 친구에게 보내기 (카카오톡 채널 친구)
    # ============================================

    def send_to_friend(self, receiver_uuid: str, problem: dict) -> dict:
        """
        친구에게 보내기
        - 카카오톡 채널 친구 추가한 사용자에게 발송
        - 사전에 메시지 발송 동의 필요
        """
        url = f"{self.base_url}/v1/api/talk/friends/message/default/send"

        template = self._build_problem_template(problem)

        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "receiver_uuids": f'["{receiver_uuid}"]',
                "template_object": template
            }
        )

        return response.json()

    # ============================================
    # 방법 3: 알림톡 (비즈니스용, 유료)
    # ============================================

    def send_alimtalk(
        self,
        phone_number: str,
        problem: dict,
        template_code: str = "DAILY_PROBLEM"
    ) -> dict:
        """
        알림톡 발송 (NHN Cloud 연동 예시)
        - 템플릿 사전 등록 필요
        - 건당 8~15원 유료
        """
        # NHN Cloud 알림톡 API 예시
        nhn_app_key = os.getenv("NHN_ALIMTALK_APP_KEY")
        nhn_secret_key = os.getenv("NHN_ALIMTALK_SECRET_KEY")
        sender_key = os.getenv("KAKAO_SENDER_KEY")

        url = f"https://api-alimtalk.cloud.toast.com/alimtalk/v2.2/appkeys/{nhn_app_key}/messages"

        # 템플릿 변수 치환
        template_vars = {
            "#{문제번호}": problem["problem_id"],
            "#{연도}": str(problem["year"]),
            "#{시험}": self._exam_type_ko(problem["exam_type"]),
            "#{단원}": problem["unit"],
            "#{배점}": str(problem["score"]),
        }

        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json;charset=UTF-8",
                "X-Secret-Key": nhn_secret_key
            },
            json={
                "senderKey": sender_key,
                "templateCode": template_code,
                "recipientList": [{
                    "recipientNo": phone_number,
                    "templateParameter": template_vars
                }]
            }
        )

        return response.json()

    # ============================================
    # 메시지 템플릿 빌더
    # ============================================

    def _build_problem_template(self, problem: dict) -> str:
        """피드 타입 메시지 템플릿 생성"""
        import json

        # 이미지가 있으면 이미지 포함, 없으면 텍스트만
        if problem.get("problem_image_url"):
            template = {
                "object_type": "feed",
                "content": {
                    "title": f"오늘의 수학 문제 ({problem['score']}점)",
                    "description": f"{problem['year']}학년도 {self._exam_type_ko(problem.get('exam_type', problem.get('exam', '')))} {problem['question_no']}번\n[{problem['subject']}] {problem['unit']}",
                    "image_url": problem["problem_image_url"],
                    "image_width": 800,
                    "image_height": 600,
                    "link": {
                        "web_url": problem.get("solve_url", "https://your-app.com"),
                        "mobile_web_url": problem.get("solve_url", "https://your-app.com")
                    }
                },
                "buttons": [
                    {
                        "title": "문제 풀기",
                        "link": {
                            "web_url": problem.get("solve_url", "https://your-app.com"),
                            "mobile_web_url": problem.get("solve_url", "https://your-app.com")
                        }
                    }
                ]
            }
        else:
            # 텍스트 타입 (이미지 없을 때)
            problem_text = MathFormatter.format_math(problem.get('problem_text', '문제를 확인하세요!'))
            template = {
                "object_type": "text",
                "text": f"📚 오늘의 수학 문제\n\n{problem['year']}학년도 {self._exam_type_ko(problem.get('exam_type', problem.get('exam', '')))} {problem['question_no']}번\n[{problem['subject']}] {problem['unit']} ({problem['score']}점)\n\n{problem_text}",
                "link": {
                    "web_url": problem.get("solve_url", "https://your-app.com"),
                    "mobile_web_url": problem.get("solve_url", "https://your-app.com")
                },
                "button_title": "문제 풀기"
            }

        return json.dumps(template)

    def _build_hint_template(self, problem: dict, hint_stage: int, hint_text: str) -> str:
        """힌트 메시지 템플릿 생성"""
        import json

        stage_names = {1: "개념 방향", 2: "핵심 전환", 3: "결정적 한 줄"}
        stage_name = stage_names.get(hint_stage, f"힌트 {hint_stage}")

        # 수학 기호 변환 적용
        formatted_hint = MathFormatter.format_hint(hint_text)

        template = {
            "object_type": "text",
            "text": f"💡 힌트 {hint_stage} - {stage_name}\n\n{problem['problem_id']}\n\n{formatted_hint}",
            "link": {
                "web_url": problem.get("solve_url", "https://your-app.com"),
                "mobile_web_url": problem.get("solve_url", "https://your-app.com")
            },
            "button_title": "문제로 돌아가기"
        }

        return json.dumps(template)

    def _build_solution_template(self, problem: dict, solution: str) -> str:
        """풀이 메시지 템플릿 생성"""
        import json

        # 수학 기호 변환 적용
        formatted_solution = MathFormatter.format_solution(solution)

        # 카카오톡 텍스트 길이 제한 (약 2000자)
        if len(formatted_solution) > 1800:
            formatted_solution = formatted_solution[:1800] + "\n\n... (전체 풀이는 앱에서 확인)"

        template = {
            "object_type": "text",
            "text": f"📝 풀이\n\n{problem['problem_id']}\n정답: {problem.get('answer', '?')}\n\n{formatted_solution}",
            "link": {
                "web_url": problem.get("solve_url", "https://your-app.com"),
                "mobile_web_url": problem.get("solve_url", "https://your-app.com")
            },
            "button_title": "다음 문제 보기"
        }

        return json.dumps(template)

    def send_hint(self, problem: dict, hint_stage: int, hint_text: str) -> dict:
        """힌트 발송"""
        url = f"{self.base_url}/v2/api/talk/memo/default/send"
        template = self._build_hint_template(problem, hint_stage, hint_text)

        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={"template_object": template}
        )
        return response.json()

    def send_solution(self, problem: dict, solution: str) -> dict:
        """풀이 발송"""
        url = f"{self.base_url}/v2/api/talk/memo/default/send"
        template = self._build_solution_template(problem, solution)

        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={"template_object": template}
        )
        return response.json()

    # ============================================
    # 복잡한 수식 이미지 발송
    # ============================================

    def _build_image_template(
        self,
        title: str,
        description: str,
        image_url: str,
        link_url: str = None
    ) -> str:
        """이미지 포함 피드 메시지 템플릿 생성"""
        import json

        template = {
            "object_type": "feed",
            "content": {
                "title": title,
                "description": description,
                "image_url": image_url,
                "image_width": 800,
                "image_height": 400,
                "link": {
                    "web_url": link_url or "https://your-app.com",
                    "mobile_web_url": link_url or "https://your-app.com"
                }
            },
            "buttons": [
                {
                    "title": "자세히 보기",
                    "link": {
                        "web_url": link_url or "https://your-app.com",
                        "mobile_web_url": link_url or "https://your-app.com"
                    }
                }
            ]
        }
        return json.dumps(template)

    def send_hint_smart(
        self,
        problem: dict,
        hint_stage: int,
        hint_text: str,
        image_generator: 'MathImageGenerator' = None
    ) -> dict:
        """
        힌트 스마트 발송 - 복잡한 수식은 이미지로

        Args:
            problem: 문제 정보
            hint_stage: 힌트 단계 (1, 2, 3)
            hint_text: 힌트 텍스트
            image_generator: MathImageGenerator 인스턴스 (없으면 자동 생성)

        Returns:
            API 응답
        """
        url = f"{self.base_url}/v2/api/talk/memo/default/send"

        # 복잡한 수식이 포함되어 있는지 확인
        if MathFormatter.has_complex_math(hint_text):
            # 이미지로 발송
            if image_generator is None:
                image_generator = MathImageGenerator()

            # LaTeX로 변환
            latex_text = SolutionToLatex.convert(hint_text)

            # 이미지 URL 생성
            image_url = image_generator.latex_to_image_url(latex_text)

            stage_names = {1: "개념 방향", 2: "핵심 전환", 3: "결정적 한 줄"}
            stage_name = stage_names.get(hint_stage, f"힌트 {hint_stage}")

            template = self._build_image_template(
                title=f"💡 힌트 {hint_stage} - {stage_name}",
                description=f"{problem['problem_id']}",
                image_url=image_url,
                link_url=problem.get("solve_url")
            )
        else:
            # 일반 텍스트 발송 (기존 방식)
            template = self._build_hint_template(problem, hint_stage, hint_text)

        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={"template_object": template}
        )
        return response.json()

    def send_solution_smart(
        self,
        problem: dict,
        solution: str,
        image_generator: 'MathImageGenerator' = None
    ) -> dict:
        """
        풀이 스마트 발송 - 복잡한 수식은 이미지로

        Args:
            problem: 문제 정보
            solution: 풀이 텍스트
            image_generator: MathImageGenerator 인스턴스 (없으면 자동 생성)

        Returns:
            API 응답
        """
        url = f"{self.base_url}/v2/api/talk/memo/default/send"

        # 복잡한 수식이 포함되어 있는지 확인
        if MathFormatter.has_complex_math(solution):
            # 이미지로 발송
            if image_generator is None:
                image_generator = MathImageGenerator()

            # 풀이가 긴 경우 여러 이미지로 분할
            images = self._split_solution_to_images(solution, image_generator)

            if len(images) == 1:
                # 단일 이미지 발송
                template = self._build_image_template(
                    title=f"📝 풀이 - {problem['problem_id']}",
                    description=f"정답: {problem.get('answer', '?')}",
                    image_url=images[0],
                    link_url=problem.get("solve_url")
                )
                response = requests.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    data={"template_object": template}
                )
                return response.json()
            else:
                # 여러 이미지 순차 발송
                results = []
                for i, img_url in enumerate(images, 1):
                    template = self._build_image_template(
                        title=f"📝 풀이 ({i}/{len(images)}) - {problem['problem_id']}",
                        description=f"정답: {problem.get('answer', '?')}" if i == 1 else "",
                        image_url=img_url,
                        link_url=problem.get("solve_url")
                    )
                    response = requests.post(
                        url,
                        headers={
                            "Authorization": f"Bearer {self.access_token}",
                            "Content-Type": "application/x-www-form-urlencoded"
                        },
                        data={"template_object": template}
                    )
                    results.append(response.json())
                return {"results": results, "image_count": len(images)}
        else:
            # 일반 텍스트 발송 (기존 방식)
            template = self._build_solution_template(problem, solution)
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={"template_object": template}
            )
            return response.json()

    def _split_solution_to_images(
        self,
        solution: str,
        image_generator: 'MathImageGenerator',
        max_chars: int = 500
    ) -> list:
        """
        긴 풀이를 여러 이미지로 분할

        Args:
            solution: 전체 풀이 텍스트
            image_generator: MathImageGenerator 인스턴스
            max_chars: 이미지당 최대 문자 수

        Returns:
            이미지 URL 리스트
        """
        # 줄바꿈 기준으로 분할
        lines = solution.split('\n')

        chunks = []
        current_chunk = []
        current_length = 0

        for line in lines:
            line_length = len(line)

            # 현재 청크에 추가하면 최대 길이 초과
            if current_length + line_length > max_chars and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_length = line_length
            else:
                current_chunk.append(line)
                current_length += line_length + 1  # +1 for newline

        # 마지막 청크 추가
        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        # 각 청크를 이미지로 변환
        images = []
        for chunk in chunks:
            latex = SolutionToLatex.convert(chunk)
            # LaTeX를 디스플레이 모드로 감싸기
            wrapped_latex = f"\\begin{{aligned}}{latex}\\end{{aligned}}"
            image_url = image_generator.latex_to_image_url(wrapped_latex)
            images.append(image_url)

        return images if images else [image_generator.latex_to_image_url(solution)]

    def send_formula_image(
        self,
        formula: str,
        title: str = "수식",
        description: str = "",
        image_generator: 'MathImageGenerator' = None
    ) -> dict:
        """
        단일 수식을 이미지로 발송

        Args:
            formula: 수식 텍스트 (일반 텍스트 또는 LaTeX)
            title: 메시지 제목
            description: 메시지 설명
            image_generator: MathImageGenerator 인스턴스

        Returns:
            API 응답
        """
        url = f"{self.base_url}/v2/api/talk/memo/default/send"

        if image_generator is None:
            image_generator = MathImageGenerator()

        # LaTeX로 변환
        latex_formula = SolutionToLatex.convert(formula)
        image_url = image_generator.latex_to_image_url(latex_formula)

        template = self._build_image_template(
            title=title,
            description=description,
            image_url=image_url
        )

        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={"template_object": template}
        )
        return response.json()

    def _exam_type_ko(self, exam_type: str) -> str:
        """시험 유형 한글 변환"""
        mapping = {
            "CSAT": "수능",
            "KICE6": "6월 모의평가",
            "KICE9": "9월 모의평가"
        }
        return mapping.get(exam_type, exam_type)


# ============================================
# 카카오 로그인 (OAuth) 헬퍼
# ============================================

class KakaoAuth:
    """카카오 OAuth 인증 헬퍼"""

    def __init__(self):
        self.rest_api_key = os.getenv("KAKAO_REST_API_KEY")
        self.redirect_uri = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:8000/auth/kakao/callback")

    def get_authorization_url(self) -> str:
        """카카오 로그인 URL 생성"""
        return (
            f"https://kauth.kakao.com/oauth/authorize"
            f"?client_id={self.rest_api_key}"
            f"&redirect_uri={self.redirect_uri}"
            f"&response_type=code"
            f"&scope=talk_message,friends"  # 메시지 발송 권한
        )

    def get_access_token(self, auth_code: str) -> dict:
        """인가 코드로 액세스 토큰 발급"""
        response = requests.post(
            "https://kauth.kakao.com/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": self.rest_api_key,
                "redirect_uri": self.redirect_uri,
                "code": auth_code
            }
        )
        return response.json()

    def refresh_access_token(self, refresh_token: str) -> dict:
        """리프레시 토큰으로 액세스 토큰 갱신"""
        response = requests.post(
            "https://kauth.kakao.com/oauth/token",
            data={
                "grant_type": "refresh_token",
                "client_id": self.rest_api_key,
                "refresh_token": refresh_token
            }
        )
        return response.json()

    def get_user_info(self, access_token: str) -> dict:
        """사용자 정보 조회"""
        response = requests.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        return response.json()


# ============================================
# 적응형 학습 관리 서비스
# ============================================

class AdaptiveLearningService:
    """
    적응형 학습 관리 서비스

    - 정답/오답에 따른 난이도 조절
    - 사용자 수준에 맞는 문제 추천
    - 취약 단원 분석 및 보강
    """

    # 난이도 레벨 설명
    DIFFICULTY_LABELS = {
        1: "매우 쉬움",
        2: "쉬움",
        3: "보통",
        4: "어려움",
        5: "매우 어려움"
    }

    # 배점별 레벨
    SCORE_LABELS = {
        2: "2점 (기본)",
        3: "3점 (표준)",
        4: "4점 (고난도)"
    }

    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """
        Args:
            supabase_url: Supabase 프로젝트 URL
            supabase_key: Supabase anon key
        """
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
        self.headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json"
        }

    def process_answer(self, delivery_id: str, user_answer: str, time_spent: int = None) -> dict:
        """
        정답 처리 및 사용자 수준 업데이트

        Args:
            delivery_id: 발송 ID
            user_answer: 사용자 답변
            time_spent: 풀이 소요 시간 (초)

        Returns:
            처리 결과 (정답 여부, 새 레벨 등)
        """
        url = f"{self.supabase_url}/rest/v1/rpc/process_answer"

        response = requests.post(
            url,
            headers=self.headers,
            json={
                "p_delivery_id": delivery_id,
                "p_user_answer": user_answer,
                "p_time_spent": time_spent
            }
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text}

    def get_next_problem(self, user_id: str, subject: str = None) -> dict:
        """
        적응형 다음 문제 추천

        Args:
            user_id: 사용자 ID
            subject: 과목 필터 (Math1, Math2, None=전체)

        Returns:
            추천 문제 정보
        """
        url = f"{self.supabase_url}/rest/v1/rpc/recommend_next_problem"

        params = {"p_user_id": user_id}
        if subject:
            params["p_subject"] = subject

        response = requests.post(
            url,
            headers=self.headers,
            json=params
        )

        if response.status_code == 200:
            result = response.json()
            if result:
                return result[0] if isinstance(result, list) else result
            return None
        else:
            return {"error": response.text}

    def get_user_stats(self, user_id: str) -> dict:
        """
        사용자 학습 현황 조회

        Args:
            user_id: 사용자 ID

        Returns:
            학습 현황 정보
        """
        url = f"{self.supabase_url}/rest/v1/user_learning_dashboard"

        response = requests.get(
            url,
            headers=self.headers,
            params={"user_id": f"eq.{user_id}"}
        )

        if response.status_code == 200:
            result = response.json()
            return result[0] if result else None
        else:
            return {"error": response.text}

    def get_weak_units(self, user_id: str, threshold: float = 0.5) -> list:
        """
        취약 단원 분석

        Args:
            user_id: 사용자 ID
            threshold: 정답률 기준 (기본 50%)

        Returns:
            취약 단원 목록
        """
        stats = self.get_user_stats(user_id)
        if not stats or "error" in stats:
            return []

        unit_stats = stats.get("unit_stats", {})
        weak_units = []

        for unit_key, data in unit_stats.items():
            total = data.get("total", 0)
            correct = data.get("correct", 0)

            if total >= 3:  # 최소 3문제 이상 푼 단원만
                rate = correct / total
                if rate < threshold:
                    weak_units.append({
                        "unit": unit_key,
                        "correct": correct,
                        "total": total,
                        "rate": round(rate * 100, 1)
                    })

        # 정답률 낮은 순으로 정렬
        weak_units.sort(key=lambda x: x["rate"])
        return weak_units

    def calculate_recommendation(self, user_id: str, is_correct: bool) -> dict:
        """
        다음 문제 추천 전략 계산 (로컬)

        Args:
            user_id: 사용자 ID
            is_correct: 직전 문제 정답 여부

        Returns:
            추천 전략
        """
        stats = self.get_user_stats(user_id)
        if not stats:
            return {
                "strategy": "default",
                "target_difficulty": 3,
                "target_score": 3,
                "reason": "사용자 정보 없음 - 기본 난이도로 시작"
            }

        current_level = stats.get("current_level", 3)
        current_score = stats.get("current_score_level", 3)
        consecutive_correct = stats.get("consecutive_correct", 0)
        consecutive_wrong = stats.get("consecutive_wrong", 0)

        if is_correct:
            # 정답인 경우
            if consecutive_correct >= 2:
                # 2연속 정답 → 도전
                if current_level < 5:
                    return {
                        "strategy": "level_up",
                        "target_difficulty": current_level + 1,
                        "target_score": current_score,
                        "reason": f"연속 {consecutive_correct + 1}문제 정답! 난이도 상승 ({self.DIFFICULTY_LABELS[current_level]} → {self.DIFFICULTY_LABELS[current_level + 1]})"
                    }
                elif current_score < 4:
                    return {
                        "strategy": "score_up",
                        "target_difficulty": 3,
                        "target_score": current_score + 1,
                        "reason": f"최고 난이도 달성! 배점 상승 ({current_score}점 → {current_score + 1}점)"
                    }
            return {
                "strategy": "maintain",
                "target_difficulty": current_level,
                "target_score": current_score,
                "reason": f"정답! 현재 수준 유지 ({self.DIFFICULTY_LABELS[current_level]}, {current_score}점)"
            }
        else:
            # 오답인 경우
            if consecutive_wrong >= 2:
                # 2연속 오답 → 난이도 하락
                if current_level > 1:
                    return {
                        "strategy": "level_down",
                        "target_difficulty": current_level - 1,
                        "target_score": current_score,
                        "reason": f"연속 {consecutive_wrong + 1}문제 오답. 난이도 조정 ({self.DIFFICULTY_LABELS[current_level]} → {self.DIFFICULTY_LABELS[current_level - 1]})"
                    }
                elif current_score > 2:
                    return {
                        "strategy": "score_down",
                        "target_difficulty": 3,
                        "target_score": current_score - 1,
                        "reason": f"기초 다지기 권장. 배점 조정 ({current_score}점 → {current_score - 1}점)"
                    }
            return {
                "strategy": "similar",
                "target_difficulty": current_level,
                "target_score": current_score,
                "reason": f"오답. 비슷한 난이도 문제로 복습 ({self.DIFFICULTY_LABELS[current_level]}, {current_score}점)"
            }

    def get_feedback_message(self, is_correct: bool, recommendation: dict) -> str:
        """
        피드백 메시지 생성

        Args:
            is_correct: 정답 여부
            recommendation: 추천 전략

        Returns:
            카카오톡 발송용 피드백 메시지
        """
        if is_correct:
            emoji = "🎉"
            result = "정답입니다!"
        else:
            emoji = "💪"
            result = "아쉽게 틀렸어요."

        strategy = recommendation.get("strategy", "maintain")
        reason = recommendation.get("reason", "")

        messages = {
            "level_up": f"{emoji} {result}\n\n📈 실력이 향상되고 있어요!\n{reason}",
            "score_up": f"{emoji} {result}\n\n🏆 대단해요! 더 높은 배점에 도전합니다.\n{reason}",
            "maintain": f"{emoji} {result}\n\n📊 {reason}",
            "similar": f"{emoji} {result}\n\n📝 비슷한 유형으로 한 번 더 연습해볼게요.\n{reason}",
            "level_down": f"{emoji} {result}\n\n📖 기초를 탄탄히 다져볼게요.\n{reason}",
            "score_down": f"{emoji} {result}\n\n📘 천천히 다시 시작해볼게요.\n{reason}",
            "default": f"{emoji} {result}\n\n{reason}"
        }

        return messages.get(strategy, messages["default"])


# ============================================
# 사용 예시
# ============================================

def test_complex_math_detection():
    """복잡한 수식 감지 테스트"""
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 50)
    print("복잡한 수식 감지 테스트")
    print("=" * 50)

    test_cases = [
        # (텍스트, 복잡 여부 예상)
        ("x^2 + y^2 = r^2", False),                      # 간단한 수식
        ("a_n = a_1 + (n-1)d", False),                   # 간단한 아래첨자
        (r"\frac{a}{b}", True),                          # 분수
        (r"\sqrt{x^2 + 1}", True),                       # 제곱근 (중괄호)
        (r"\sum_{i=1}^{n} i", True),                     # 시그마
        (r"\int_{0}^{1} x dx", True),                    # 적분
        (r"\lim_{x \to 0} \frac{sin x}{x}", True),       # 극한
        (r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}", True),  # 행렬
        (r"\binom{n}{r}", True),                         # 이항계수
    ]

    for text, expected in test_cases:
        result = MathFormatter.has_complex_math(text)
        status = "✓" if result == expected else "✗"
        print(f"\n{status} '{text[:40]}...' " if len(text) > 40 else f"\n{status} '{text}'")
        print(f"   예상: {expected}, 결과: {result}")

    print("\n" + "=" * 50)


def test_image_url_generation():
    """이미지 URL 생성 테스트"""
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 50)
    print("이미지 URL 생성 테스트")
    print("=" * 50)

    generator = MathImageGenerator()

    test_formulas = [
        r"\frac{a}{b}",
        r"\sqrt{x^2 + y^2}",
        r"\sum_{i=1}^{n} i = \frac{n(n+1)}{2}",
        r"\int_{0}^{1} x^2 dx = \frac{1}{3}",
        r"\lim_{x \to 0} \frac{\sin x}{x} = 1",
    ]

    for formula in test_formulas:
        print(f"\n수식: {formula}")
        url = generator.latex_to_image_url(formula)
        print(f"URL: {url[:80]}...")

    print("\n" + "=" * 50)


def test_math_formatter():
    """수학 기호 변환 테스트"""
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 50)
    print("수학 기호 변환 테스트")
    print("=" * 50)

    test_cases = [
        # (원본, 설명)
        ("2^x = 8", "거듭제곱"),
        ("x^2 + y^2 = r^2", "제곱"),
        ("a^{n+1} = a^n * a", "복합 지수"),
        ("a_n = a_1 + (n-1)d", "수열 아래첨자"),
        ("lim(x→2) (x^2-4)/(x-2)", "극한"),
        ("f'(x) = 3x^2 - 4x + 1", "도함수"),
        ("log_2(8) = 3", "로그"),
        ("sin^2(x) + cos^2(x) = 1", "삼각함수"),
        ("\\int x^2 dx = x^3/3 + C", "적분"),
        ("\\sqrt{x^2 + y^2}", "제곱근"),
    ]

    for original, description in test_cases:
        converted = MathFormatter.format_math(original)
        print(f"\n[{description}]")
        print(f"  원본: {original}")
        print(f"  변환: {converted}")

    print("\n" + "=" * 50)


def example_usage():
    """사용 예시"""
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    # 1. 복잡한 수식 감지 테스트
    test_complex_math_detection()

    # 2. 이미지 URL 생성 테스트
    test_image_url_generation()

    # 3. 수학 기호 변환 테스트
    test_math_formatter()

    # 문제 데이터 예시
    problem = {
        "problem_id": "2024_CSAT_COMMON_Q13",
        "year": 2024,
        "exam_type": "CSAT",
        "question_no": 13,
        "subject": "Math2",
        "unit": "미분",
        "score": 4,
        "problem_image_url": "https://your-storage.supabase.co/problems/2024_CSAT_Q13.png",
        "solve_url": "https://your-app.com/solve/2024_CSAT_COMMON_Q13",
        "answer": "③"
    }

    # 4. 카카오 로그인 URL 생성
    auth = KakaoAuth()
    login_url = auth.get_authorization_url()
    print(f"\n카카오 로그인: {login_url}")

    # 5. 스마트 발송 예시 (복잡한 수식 → 이미지, 단순 수식 → 텍스트)
    print("\n" + "=" * 50)
    print("스마트 발송 기능 설명")
    print("=" * 50)
    print("""
    KakaoMessageService 클래스의 새 메서드:

    1. send_hint_smart(problem, hint_stage, hint_text)
       - 복잡한 수식 포함 시 → 이미지로 발송
       - 단순 수식만 있으면 → 유니코드 텍스트로 발송

    2. send_solution_smart(problem, solution)
       - 복잡한 수식 포함 시 → 이미지로 발송
       - 긴 풀이는 여러 이미지로 자동 분할
       - 단순 수식만 있으면 → 유니코드 텍스트로 발송

    3. send_formula_image(formula, title, description)
       - 단일 수식을 무조건 이미지로 발송

    복잡한 수식으로 판단되는 패턴:
    - \\frac{} : 분수
    - \\sqrt{} : 제곱근
    - \\sum_, \\prod_ : 시그마, 파이
    - \\int_ : 적분
    - \\lim_ : 극한
    - \\begin{} : 행렬, 정렬 등
    - \\binom : 이항계수
    """)

    # 메시지 발송 (액세스 토큰 필요)
    # kakao = KakaoMessageService()

    # 복잡한 수식이 포함된 힌트 발송 예시
    # complex_hint = r"\\frac{d}{dx}[f(g(x))] = f'(g(x)) \\cdot g'(x)"
    # result = kakao.send_hint_smart(problem, 1, complex_hint)
    # print(result)

    # 복잡한 수식이 포함된 풀이 발송 예시
    # complex_solution = r"""
    # 【풀이】
    # 합성함수의 미분법을 적용한다.
    #
    # \\frac{d}{dx}[f(g(x))] = f'(g(x)) \\cdot g'(x)
    #
    # g(x) = x^2 + 1이므로 g'(x) = 2x
    # f(u) = \\sqrt{u}이므로 f'(u) = \\frac{1}{2\\sqrt{u}}
    #
    # 따라서 답은 \\frac{2x}{2\\sqrt{x^2+1}} = \\frac{x}{\\sqrt{x^2+1}}
    # """
    # result = kakao.send_solution_smart(problem, complex_solution)
    # print(result)


if __name__ == "__main__":
    example_usage()
