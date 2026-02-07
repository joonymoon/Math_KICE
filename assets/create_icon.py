"""
Pillow로 직접 PNG 아이콘 생성
카카오 앱 아이콘용 512x512 PNG
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size=512):
    """수학 아이콘 생성"""

    # 새 이미지 생성 (RGBA)
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 배경 그라데이션 (보라색 계열)
    for y in range(size):
        # 그라데이션: #667eea -> #764ba2
        ratio = y / size
        r = int(102 + (118 - 102) * ratio)
        g = int(126 + (75 - 126) * ratio)
        b = int(234 + (162 - 234) * ratio)
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

    # 둥근 모서리 마스크 적용
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    corner_radius = size // 5  # 100px for 512
    mask_draw.rounded_rectangle([0, 0, size, size], radius=corner_radius, fill=255)

    # 마스크 적용
    result = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    result.paste(img, mask=mask)

    draw = ImageDraw.Draw(result)

    # 흰색 원 (수학 기호 배경)
    center_x, center_y = size // 2, int(size * 0.45)  # 약간 위쪽
    circle_radius = int(size * 0.27)  # 140px for 512
    draw.ellipse(
        [center_x - circle_radius, center_y - circle_radius,
         center_x + circle_radius, center_y + circle_radius],
        fill=(255, 255, 255, 242)
    )

    # 폰트 설정 (시스템 폰트 사용)
    try:
        # Windows 시스템 폰트
        symbol_font = ImageFont.truetype("times.ttf", int(size * 0.35))
        title_font = ImageFont.truetype("arial.ttf", int(size * 0.14))
        subtitle_font = ImageFont.truetype("arial.ttf", int(size * 0.07))
    except:
        try:
            # 대체 폰트
            symbol_font = ImageFont.truetype("C:/Windows/Fonts/times.ttf", int(size * 0.35))
            title_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(size * 0.14))
            subtitle_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(size * 0.07))
        except:
            # 기본 폰트 (작을 수 있음)
            symbol_font = ImageFont.load_default()
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()

    # 시그마 기호 (수학 상징)
    sigma = "Σ"
    try:
        bbox = draw.textbbox((0, 0), sigma, font=symbol_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = center_x - text_width // 2
        y = center_y - text_height // 2 - int(size * 0.02)
        draw.text((x, y), sigma, fill=(102, 126, 234, 255), font=symbol_font)
    except:
        # textbbox 없는 경우
        draw.text((center_x - 50, center_y - 60), sigma, fill=(102, 126, 234, 255), font=symbol_font)

    # "KICE" 텍스트
    kice_text = "KICE"
    kice_y = int(size * 0.75)
    try:
        bbox = draw.textbbox((0, 0), kice_text, font=title_font)
        text_width = bbox[2] - bbox[0]
        x = center_x - text_width // 2
        draw.text((x, kice_y), kice_text, fill=(255, 255, 255, 255), font=title_font)
    except:
        draw.text((center_x - 80, kice_y), kice_text, fill=(255, 255, 255, 255), font=title_font)

    # "Math" 서브타이틀
    math_text = "Math"
    math_y = int(size * 0.88)
    try:
        bbox = draw.textbbox((0, 0), math_text, font=subtitle_font)
        text_width = bbox[2] - bbox[0]
        x = center_x - text_width // 2
        draw.text((x, math_y), math_text, fill=(255, 255, 255, 230), font=subtitle_font)
    except:
        draw.text((center_x - 40, math_y), math_text, fill=(255, 255, 255, 230), font=subtitle_font)

    return result


if __name__ == "__main__":
    print("카카오 앱 아이콘 생성 중...")

    # 512x512 아이콘 생성
    icon = create_icon(512)

    # 저장
    output_path = os.path.join(os.path.dirname(__file__), "app_icon.png")
    icon.save(output_path, "PNG")
    print(f"아이콘 생성 완료: {output_path}")

    # 추가 크기 생성 (선택)
    for size in [256, 128, 64]:
        small_icon = create_icon(size)
        small_path = os.path.join(os.path.dirname(__file__), f"app_icon_{size}.png")
        small_icon.save(small_path, "PNG")
        print(f"  - {size}x{size}: {small_path}")

    print("\n카카오 개발자 콘솔에 app_icon.png 를 업로드하세요.")
