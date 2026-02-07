"""
설정 관리 모듈
환경 변수 로드 및 설정값 관리
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# ============================================
# 프로젝트 경로
# ============================================
BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOAD_PATH = Path(os.getenv("DOWNLOAD_PATH", BASE_DIR / "downloads"))
OUTPUT_PATH = Path(os.getenv("OUTPUT_PATH", BASE_DIR / "output"))
CREDENTIALS_PATH = BASE_DIR / "credentials"

# 폴더 생성
DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
CREDENTIALS_PATH.mkdir(parents=True, exist_ok=True)

# ============================================
# Supabase 설정
# ============================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# ============================================
# Google Drive 설정
# ============================================
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
GOOGLE_DRIVE_OUTPUT_FOLDER_ID = os.getenv("GOOGLE_DRIVE_OUTPUT_FOLDER_ID")

# Google Drive 서브폴더 ID (KICE_Math 내부 구조)
GDRIVE_PROBLEMS_FOLDER_ID = os.getenv(
    "GDRIVE_PROBLEMS_FOLDER_ID", "14wJp-zdOi1Gox53e1TmzuuD_ga8T7DFp")
GDRIVE_ANSWERS_FOLDER_ID = os.getenv(
    "GDRIVE_ANSWERS_FOLDER_ID", "1-dpCnFhwjJsEoK_QT8rNJQogB2G1vFy0")
GDRIVE_PROCESSED_FOLDER_ID = os.getenv(
    "GDRIVE_PROCESSED_FOLDER_ID", "1wFkir3m_HEPiAQuI97SV9c7miiuarRmk")

# OAuth 토큰 저장 경로
GOOGLE_TOKEN_PATH = CREDENTIALS_PATH / "google_token.json"
GOOGLE_CREDENTIALS_PATH = CREDENTIALS_PATH / "google_credentials.json"

# Google Drive API 스코프
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file",
]

# ============================================
# Notion 설정
# ============================================
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# ============================================
# 카카오 설정
# ============================================
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
KAKAO_ACCESS_TOKEN = os.getenv("KAKAO_ACCESS_TOKEN")
KAKAO_REFRESH_TOKEN = os.getenv("KAKAO_REFRESH_TOKEN")

# ============================================
# 개발 설정
# ============================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# ============================================
# PDF 변환 설정
# ============================================
PDF_DPI = 200  # 이미지 해상도
PDF_IMAGE_FORMAT = "png"

# ============================================
# 파일명 파싱 패턴
# ============================================
# 예: 2024_CSAT_PROBLEM.pdf → year=2024, exam=CSAT, type=PROBLEM
FILENAME_PATTERN = r"(\d{4})_(\w+)_(\w+)\.pdf"

# 시험 유형 매핑
EXAM_TYPE_MAP = {
    "CSAT": "수능",
    "KICE6": "6월 평가원",
    "KICE9": "9월 평가원",
}


def validate_config():
    """필수 설정값 검증"""
    errors = []

    if not SUPABASE_URL:
        errors.append("SUPABASE_URL이 설정되지 않았습니다.")
    if not SUPABASE_KEY:
        errors.append("SUPABASE_KEY가 설정되지 않았습니다.")
    if not GOOGLE_CLIENT_ID:
        errors.append("GOOGLE_CLIENT_ID가 설정되지 않았습니다.")
    if not GOOGLE_CLIENT_SECRET:
        errors.append("GOOGLE_CLIENT_SECRET이 설정되지 않았습니다.")
    if not GOOGLE_DRIVE_FOLDER_ID:
        errors.append("GOOGLE_DRIVE_FOLDER_ID가 설정되지 않았습니다.")
    if not NOTION_TOKEN:
        errors.append("NOTION_TOKEN이 설정되지 않았습니다.")
    if not NOTION_DATABASE_ID:
        errors.append("NOTION_DATABASE_ID가 설정되지 않았습니다.")

    if errors:
        print("설정 오류:")
        for error in errors:
            print(f"  - {error}")
        print("\n.env 파일을 확인하세요.")
        return False

    return True


def print_config():
    """현재 설정 출력 (디버그용)"""
    print("=" * 50)
    print("KICE 수학 문제 관리 시스템 설정")
    print("=" * 50)
    print(f"Supabase URL: {SUPABASE_URL[:30]}..." if SUPABASE_URL else "Supabase URL: 미설정")
    print(f"Google Drive 폴더: {GOOGLE_DRIVE_FOLDER_ID}")
    print(f"Notion Database: {NOTION_DATABASE_ID}")
    print(f"다운로드 경로: {DOWNLOAD_PATH}")
    print(f"출력 경로: {OUTPUT_PATH}")
    print(f"디버그 모드: {DEBUG}")
    print("=" * 50)
