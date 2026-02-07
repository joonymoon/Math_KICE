"""
SVG to PNG 변환 스크립트
카카오 앱 아이콘용 512x512 PNG 생성
"""

import os
import sys

def convert_with_cairosvg():
    """cairosvg 라이브러리 사용"""
    try:
        import cairosvg

        svg_path = os.path.join(os.path.dirname(__file__), "app_icon.svg")
        png_path = os.path.join(os.path.dirname(__file__), "app_icon.png")

        cairosvg.svg2png(
            url=svg_path,
            write_to=png_path,
            output_width=512,
            output_height=512
        )
        print(f"PNG 아이콘 생성 완료: {png_path}")
        return True
    except ImportError:
        print("cairosvg가 설치되어 있지 않습니다.")
        return False
    except Exception as e:
        print(f"변환 오류: {e}")
        return False


def convert_with_pillow_and_reportlab():
    """Pillow + svglib 사용"""
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM

        svg_path = os.path.join(os.path.dirname(__file__), "app_icon.svg")
        png_path = os.path.join(os.path.dirname(__file__), "app_icon.png")

        drawing = svg2rlg(svg_path)
        renderPM.drawToFile(drawing, png_path, fmt="PNG")
        print(f"PNG 아이콘 생성 완료: {png_path}")
        return True
    except ImportError:
        print("svglib/reportlab가 설치되어 있지 않습니다.")
        return False
    except Exception as e:
        print(f"변환 오류: {e}")
        return False


def print_manual_instructions():
    """수동 변환 방법 안내"""
    print("\n" + "=" * 50)
    print("PNG 변환 방법 (온라인 도구 사용)")
    print("=" * 50)
    print("""
1. 브라우저에서 다음 사이트 중 하나 접속:
   - https://cloudconvert.com/svg-to-png
   - https://svgtopng.com/
   - https://convertio.co/kr/svg-png/

2. assets/app_icon.svg 파일 업로드

3. 크기를 512x512로 설정

4. PNG로 변환 후 다운로드

5. 다운로드한 파일을 assets/app_icon.png로 저장

또는 브라우저에서 SVG 파일을 열고:
1. 파일 탐색기에서 app_icon.svg를 브라우저로 드래그
2. 스크린샷을 찍거나 개발자 도구로 저장
""")


if __name__ == "__main__":
    print("카카오 앱 아이콘 PNG 변환")
    print("-" * 30)

    # 방법 1: cairosvg 시도
    if convert_with_cairosvg():
        sys.exit(0)

    # 방법 2: svglib 시도
    print("\ncairosvg 실패, svglib 시도 중...")
    if convert_with_pillow_and_reportlab():
        sys.exit(0)

    # 수동 방법 안내
    print_manual_instructions()

    print("\n라이브러리 설치 명령어:")
    print("  pip install cairosvg")
    print("  또는")
    print("  pip install svglib reportlab")
