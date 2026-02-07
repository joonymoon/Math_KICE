"""
Google Drive 연동 서비스
- OAuth 인증
- 파일 목록 조회
- 파일 다운로드
- 파일 업로드
"""

import os
import io
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from .config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_SCOPES,
    GOOGLE_TOKEN_PATH,
    GOOGLE_CREDENTIALS_PATH,
    GOOGLE_DRIVE_FOLDER_ID,
    DOWNLOAD_PATH,
)


class GoogleDriveService:
    """Google Drive API 서비스"""

    def __init__(self):
        self.credentials = None
        self.service = None
        self._authenticate()

    def _create_credentials_file(self):
        """OAuth 클라이언트 자격 증명 파일 생성"""
        credentials_data = {
            "installed": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["http://localhost:8080/"]
            }
        }

        with open(GOOGLE_CREDENTIALS_PATH, "w") as f:
            json.dump(credentials_data, f, indent=2)

        print(f"자격 증명 파일 생성됨: {GOOGLE_CREDENTIALS_PATH}")

    def _authenticate(self):
        """OAuth 인증 수행"""
        # 기존 토큰 확인
        if GOOGLE_TOKEN_PATH.exists():
            self.credentials = Credentials.from_authorized_user_file(
                str(GOOGLE_TOKEN_PATH), GOOGLE_SCOPES
            )

        # 토큰이 없거나 만료된 경우
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                # 토큰 갱신
                print("토큰 갱신 중...")
                self.credentials.refresh(Request())
            else:
                # 새로운 인증 필요
                print("Google Drive 인증이 필요합니다.")

                # 자격 증명 파일이 없으면 생성
                if not GOOGLE_CREDENTIALS_PATH.exists():
                    self._create_credentials_file()

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(GOOGLE_CREDENTIALS_PATH), GOOGLE_SCOPES
                )
                self.credentials = flow.run_local_server(port=8080)

            # 토큰 저장
            with open(GOOGLE_TOKEN_PATH, "w") as token:
                token.write(self.credentials.to_json())
            print(f"토큰 저장됨: {GOOGLE_TOKEN_PATH}")

        # Drive API 서비스 생성
        self.service = build("drive", "v3", credentials=self.credentials)
        print("Google Drive 연결 성공!")

    def list_files(
        self,
        folder_id: Optional[str] = None,
        mime_type: Optional[str] = None,
        max_results: int = 100,
    ) -> list:
        """
        폴더 내 파일 목록 조회

        Args:
            folder_id: 폴더 ID (기본값: 환경변수 설정값)
            mime_type: 파일 타입 필터 (예: 'application/pdf')
            max_results: 최대 결과 수

        Returns:
            파일 목록 [{id, name, mimeType, createdTime, webViewLink}, ...]
        """
        folder_id = folder_id or GOOGLE_DRIVE_FOLDER_ID

        query_parts = [f"'{folder_id}' in parents", "trashed = false"]

        if mime_type:
            query_parts.append(f"mimeType = '{mime_type}'")

        query = " and ".join(query_parts)

        results = self.service.files().list(
            q=query,
            pageSize=max_results,
            fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, webViewLink, size)",
            orderBy="createdTime desc",
        ).execute()

        files = results.get("files", [])
        print(f"조회된 파일 수: {len(files)}")

        return files

    def list_pdf_files(self, folder_id: Optional[str] = None) -> list:
        """PDF 파일만 조회"""
        return self.list_files(
            folder_id=folder_id,
            mime_type="application/pdf"
        )

    def download_file(
        self,
        file_id: str,
        file_name: Optional[str] = None,
        destination: Optional[Path] = None,
    ) -> Path:
        """
        파일 다운로드

        Args:
            file_id: Google Drive 파일 ID
            file_name: 저장할 파일명 (없으면 원본 파일명 사용)
            destination: 저장 경로 (없으면 기본 다운로드 폴더)

        Returns:
            다운로드된 파일 경로
        """
        # 파일 메타데이터 조회
        file_metadata = self.service.files().get(
            fileId=file_id, fields="name, mimeType"
        ).execute()

        if not file_name:
            file_name = file_metadata["name"]

        destination = destination or DOWNLOAD_PATH
        file_path = destination / file_name

        # 파일 다운로드
        request = self.service.files().get_media(fileId=file_id)

        with open(file_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"다운로드 진행: {int(status.progress() * 100)}%")

        print(f"다운로드 완료: {file_path}")
        return file_path

    def upload_file(
        self,
        file_path: Path,
        folder_id: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> dict:
        """
        파일 업로드

        Args:
            file_path: 업로드할 파일 경로
            folder_id: 업로드할 폴더 ID
            mime_type: 파일 MIME 타입

        Returns:
            업로드된 파일 정보 {id, name, webViewLink}
        """
        file_metadata = {"name": file_path.name}

        if folder_id:
            file_metadata["parents"] = [folder_id]

        # MIME 타입 추론
        if not mime_type:
            extension = file_path.suffix.lower()
            mime_types = {
                ".pdf": "application/pdf",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
            }
            mime_type = mime_types.get(extension, "application/octet-stream")

        media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)

        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, name, webViewLink",
        ).execute()

        print(f"업로드 완료: {file.get('name')} -> {file.get('webViewLink')}")
        return file

    def create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> dict:
        """
        폴더 생성

        Args:
            folder_name: 폴더명
            parent_id: 부모 폴더 ID

        Returns:
            생성된 폴더 정보 {id, name, webViewLink}
        """
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }

        if parent_id:
            file_metadata["parents"] = [parent_id]

        folder = self.service.files().create(
            body=file_metadata,
            fields="id, name, webViewLink",
        ).execute()

        print(f"폴더 생성됨: {folder.get('name')} ({folder.get('id')})")
        return folder

    def get_or_create_folder(
        self,
        folder_name: str,
        parent_id: Optional[str] = None
    ) -> str:
        """
        폴더 조회 또는 생성

        Returns:
            폴더 ID
        """
        parent_id = parent_id or GOOGLE_DRIVE_FOLDER_ID

        # 기존 폴더 검색
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed = false"

        results = self.service.files().list(
            q=query,
            fields="files(id, name)",
        ).execute()

        files = results.get("files", [])

        if files:
            return files[0]["id"]

        # 폴더 생성
        folder = self.create_folder(folder_name, parent_id)
        return folder["id"]

    def move_file(
        self,
        file_id: str,
        new_parent_id: str,
        old_parent_id: Optional[str] = None,
    ):
        """
        파일을 다른 폴더로 이동

        Args:
            file_id: 이동할 파일 ID
            new_parent_id: 새 부모 폴더 ID
            old_parent_id: 기존 부모 폴더 ID (None이면 자동 감지)
        """
        if not old_parent_id:
            file = self.service.files().get(
                fileId=file_id, fields="parents"
            ).execute()
            old_parent_id = ",".join(file.get("parents", []))

        self.service.files().update(
            fileId=file_id,
            addParents=new_parent_id,
            removeParents=old_parent_id,
            fields="id, parents",
        ).execute()

        print(f"파일 이동 완료: {file_id}")

    def get_new_files(
        self,
        folder_id: Optional[str] = None,
        since: Optional[datetime] = None,
        processed_ids: Optional[set] = None,
    ) -> list:
        """
        새로운 파일 조회 (이미 처리된 파일 제외)

        Args:
            folder_id: 폴더 ID
            since: 이 시점 이후 생성된 파일만
            processed_ids: 이미 처리된 파일 ID 집합

        Returns:
            새로운 파일 목록
        """
        all_files = self.list_pdf_files(folder_id)

        processed_ids = processed_ids or set()

        new_files = []
        for file in all_files:
            # 이미 처리된 파일 건너뛰기
            if file["id"] in processed_ids:
                continue

            # 시간 필터
            if since:
                created_time = datetime.fromisoformat(
                    file["createdTime"].replace("Z", "+00:00")
                )
                if created_time.replace(tzinfo=None) < since:
                    continue

            new_files.append(file)

        print(f"새로운 파일: {len(new_files)}개")
        return new_files


# 편의 함수
def get_drive_service() -> GoogleDriveService:
    """GoogleDriveService 인스턴스 반환"""
    return GoogleDriveService()


if __name__ == "__main__":
    # 테스트
    service = GoogleDriveService()

    print("\n=== PDF 파일 목록 ===")
    files = service.list_pdf_files()
    for f in files[:5]:
        print(f"- {f['name']} ({f['id']})")
