"""
KICE Math KakaoTalk Service - Web Server
FastAPI-based OAuth and API server
"""

from .main import app
from .auth import router as auth_router
from .users import UserService

__all__ = ["app", "auth_router", "UserService"]
