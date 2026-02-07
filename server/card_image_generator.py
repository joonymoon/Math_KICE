"""
Card Image Generator for KakaoTalk
Generates composite card images with problem + metadata
"""

from PIL import Image, ImageDraw, ImageFont
import io
import requests
from typing import Optional


class CardImageGenerator:
    """Generate KakaoTalk-optimized card images"""

    # Card dimensions: 2x resolution for sharp display on high-DPI screens
    # KakaoTalk displays at ~800px but higher source = sharper rendering
    CARD_WIDTH = 1600
    CARD_HEIGHT = 1600

    # Colors - Modern gradient theme
    BG_COLOR = "#FFFFFF"
    HEADER_START = "#667eea"
    HEADER_END = "#764ba2"
    TITLE_COLOR = "#FFFFFF"
    META_COLOR = "#F0F4FF"
    BADGE_BG = "rgba(255, 255, 255, 0.2)"
    BORDER_COLOR = "#E2E8F0"
    FOOTER_BG = "#F8FAFC"
    FOOTER_TEXT = "#64748B"

    def __init__(self):
        pass

    def _draw_rounded_rectangle(self, draw, coords, radius=10, fill=(255, 255, 255, 100), outline=None, width=1):
        """Helper to draw rounded rectangle"""
        x1, y1 = coords[0]
        x2, y2 = coords[1]

        # Draw rounded corners
        draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=width)

    def generate_card(
        self,
        problem_image_url: str,
        title: str,
        year: int = None,
        exam: str = None,
        number: int = None,
        difficulty: str = None,
        unit: str = None
    ) -> bytes:
        """
        Generate a composite card image for KakaoTalk

        Args:
            problem_image_url: URL to problem image
            title: Problem title
            year, exam, number: Problem metadata
            difficulty: Problem difficulty
            unit: Problem unit

        Returns:
            PNG image bytes
        """
        # Create base card
        card = Image.new("RGB", (self.CARD_WIDTH, self.CARD_HEIGHT), self.BG_COLOR)
        draw = ImageDraw.Draw(card)

        # Fonts - 2x size for high-res card
        try:
            title_font = ImageFont.truetype("malgun.ttf", 56)
            meta_font = ImageFont.truetype("malgun.ttf", 36)
            small_font = ImageFont.truetype("malgun.ttf", 32)
        except:
            try:
                title_font = ImageFont.truetype("C:\\Windows\\Fonts\\malgun.ttf", 56)
                meta_font = ImageFont.truetype("C:\\Windows\\Fonts\\malgun.ttf", 36)
                small_font = ImageFont.truetype("C:\\Windows\\Fonts\\malgun.ttf", 32)
            except:
                title_font = ImageFont.load_default()
                meta_font = ImageFont.load_default()
                small_font = ImageFont.load_default()

        # 1. Draw header section with gradient (top 240px)
        header_height = 240
        for i in range(header_height):
            ratio = i / header_height
            r = int(102 + (118 - 102) * ratio)
            g = int(126 + (75 - 126) * ratio)
            b = int(234 + (162 - 234) * ratio)
            color = (r, g, b)
            draw.line([(0, i), (self.CARD_WIDTH, i)], fill=color, width=1)

        # Build title text
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

        title_text = f"{exam_emoji} {year or ''} {exam_name}"
        subtitle_text = f"문제 {number or ''}번"

        # Draw title with shadow
        draw.text((44, 44), title_text, fill=(0, 0, 0, 50), font=title_font)
        draw.text((40, 40), title_text, fill=self.TITLE_COLOR, font=title_font)

        # Subtitle
        draw.text((40, 120), subtitle_text, fill=self.META_COLOR, font=meta_font)

        # Draw metadata badges (right side)
        x_offset = self.CARD_WIDTH - 400
        y_badge = 50
        if difficulty:
            diff_emoji = {"2점": "⭐", "3점": "⭐⭐", "4점": "⭐⭐⭐"}.get(difficulty, "⭐⭐")
            badge_text = f"{diff_emoji} {difficulty}"
            self._draw_rounded_rectangle(draw, [(x_offset - 20, y_badge - 10), (x_offset + 260, y_badge + 50)],
                                         radius=24, fill=(255, 255, 255, 40))
            draw.text((x_offset, y_badge), badge_text, fill=self.TITLE_COLOR, font=small_font)
            y_badge += 80

        if unit:
            badge_text = f"📚 {unit}"
            self._draw_rounded_rectangle(draw, [(x_offset - 20, y_badge - 10), (x_offset + 260, y_badge + 50)],
                                         radius=24, fill=(255, 255, 255, 40))
            draw.text((x_offset, y_badge), badge_text, fill=self.TITLE_COLOR, font=small_font)

        # 2. Load and resize problem image (middle section)
        try:
            response = requests.get(problem_image_url, timeout=10)
            response.raise_for_status()
            problem_img = Image.open(io.BytesIO(response.content))

            # Available space: header=240, footer=240, image area=1120px
            available_width = self.CARD_WIDTH - 80  # 40px padding each side
            available_height = 1120

            # Resize maintaining aspect ratio
            img_ratio = problem_img.width / problem_img.height
            if img_ratio > available_width / available_height:
                new_width = available_width
                new_height = int(available_width / img_ratio)
            else:
                new_height = available_height
                new_width = int(available_height * img_ratio)

            problem_img = problem_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Center the image
            x_pos = (self.CARD_WIDTH - new_width) // 2
            y_pos = header_height + (1120 - new_height) // 2

            card.paste(problem_img, (x_pos, y_pos))

        except Exception as e:
            print(f"[ERROR] Failed to load problem image: {e}")
            draw.rectangle([(40, 250), (self.CARD_WIDTH - 40, 1360)], outline=self.BORDER_COLOR, width=4)
            draw.text((self.CARD_WIDTH // 2 - 100, 800), "이미지 로드 실패", fill=self.META_COLOR, font=meta_font)

        # 3. Draw footer section (bottom 240px)
        footer_y = 1360
        draw.rectangle([(0, footer_y), (self.CARD_WIDTH, self.CARD_HEIGHT)], fill=self.FOOTER_BG)

        footer_line1 = "💡 '힌트' 입력 → 힌트 보기"
        footer_line2 = "✅ '정답' 입력 → 정답 확인"
        draw.text((60, footer_y + 50), footer_line1, fill=self.FOOTER_TEXT, font=small_font)
        draw.text((60, footer_y + 110), footer_line2, fill=self.FOOTER_TEXT, font=small_font)

        # Branding
        brand_text = "KICE Math"
        brand_width = draw.textlength(brand_text, font=meta_font)
        draw.text((self.CARD_WIDTH - brand_width - 60, footer_y + 160), brand_text,
                 fill=self.FOOTER_TEXT, font=meta_font)

        # Convert to bytes
        output = io.BytesIO()
        card.save(output, format="PNG", optimize=True)
        return output.getvalue()
