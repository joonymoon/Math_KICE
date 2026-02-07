"""
Upload Cropped Images - 크롭된 이미지 업로드 도구
수동으로 크롭한 이미지를 Supabase에 업로드합니다
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

from src.supabase_storage import SupabaseStorageService


def upload_single_image(image_path: str, problem_id: str):
    """
    단일 이미지를 Supabase에 업로드

    Args:
        image_path: 크롭된 이미지 파일 경로
        problem_id: 문제 ID (예: 2026_CSAT_Q03)
    """
    if not os.path.exists(image_path):
        print(f"❌ 파일을 찾을 수 없습니다: {image_path}")
        return False

    print(f"\n{'='*60}")
    print(f"이미지 업로드 중...")
    print(f"  파일: {os.path.basename(image_path)}")
    print(f"  문제 ID: {problem_id}")
    print(f"{'='*60}\n")

    try:
        storage = SupabaseStorageService()
        storage.create_bucket_if_not_exists()

        filename = f"{problem_id}.png"

        # Upload to Supabase (will overwrite existing)
        result = storage.upload_image(
            local_path=image_path,
            remote_path=filename
        )

        if result.get("success"):
            print(f"✅ 업로드 성공!")
            print(f"   URL: {result.get('url')}")
            print(f"\n✨ 카카오톡으로 다시 발송해보세요!")
            return True
        else:
            print(f"❌ 업로드 실패: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*60)
    print("  크롭된 이미지 업로드 도구")
    print("="*60)

    if len(sys.argv) < 3:
        print("\n사용법:")
        print("  python upload_cropped.py <이미지파일경로> <문제ID>")
        print("\n예시:")
        print("  python upload_cropped.py Q03_cropped.png 2026_CSAT_Q03")
        print("  python upload_cropped.py myimage.png 2026_CSAT_Q05")
        print()

        # Interactive mode
        print("대화형 모드:")
        image_path = input("\n이미지 파일 경로: ").strip().strip('"')
        problem_id = input("문제 ID (예: 2026_CSAT_Q03): ").strip()

        if not image_path or not problem_id:
            print("❌ 입력이 취소되었습니다")
            return
    else:
        image_path = sys.argv[1]
        problem_id = sys.argv[2]

    # Upload
    success = upload_single_image(image_path, problem_id)

    if success:
        print("\n✅ 완료!")
        print("\n다음 단계:")
        print("1. http://localhost:8000/problem/admin 접속")
        print(f"2. {problem_id} 선택하여 카카오톡 발송")
        print("3. 올바른 크롭된 이미지 확인\n")
    else:
        print("\n❌ 업로드 실패\n")


if __name__ == "__main__":
    main()
