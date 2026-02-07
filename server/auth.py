"""
Kakao OAuth Authentication Routes
Handles login, callback, and logout
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

import requests
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Kakao OAuth settings
KAKAO_CLIENT_ID = os.getenv("KAKAO_REST_API_KEY", "")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET", "")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:8000/auth/kakao/callback")

# Debug: print loaded config
print(f"[Kakao Config] CLIENT_ID: {KAKAO_CLIENT_ID[:8]}... (len={len(KAKAO_CLIENT_ID)})")
print(f"[Kakao Config] REDIRECT_URI: {KAKAO_REDIRECT_URI}")

# OAuth URLs
KAKAO_AUTH_URL = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USER_URL = "https://kapi.kakao.com/v2/user/me"
KAKAO_LOGOUT_URL = "https://kapi.kakao.com/v1/user/logout"


def get_html_response(title: str, message: str, redirect_url: str = "/", is_error: bool = False) -> str:
    """Generate HTML response page"""
    bg_color = "#ffebee" if is_error else "#e8f5e9"
    text_color = "#c62828" if is_error else "#2e7d32"

    return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - KICE Math</title>
    <meta http-equiv="refresh" content="1;url={redirect_url}">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1e40af 0%, #4f46e5 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
            max-width: 400px;
        }}
        .message {{
            background: {bg_color};
            color: {text_color};
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .redirect {{
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="message">
            <h2>{title}</h2>
            <p>{message}</p>
        </div>
        <p class="redirect">잠시 후 이동합니다...</p>
    </div>
</body>
</html>
"""


@router.get("/kakao")
async def kakao_login():
    """
    Step 1: Redirect to Kakao login page
    """
    if not KAKAO_CLIENT_ID or KAKAO_CLIENT_ID == "your-rest-api-key":
        return HTMLResponse(
            content=get_html_response(
                "Configuration Error",
                "KAKAO_REST_API_KEY is not set in .env file",
                "/",
                is_error=True
            ),
            status_code=400
        )

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Build authorization URL
    auth_url = (
        f"{KAKAO_AUTH_URL}"
        f"?client_id={KAKAO_CLIENT_ID}"
        f"&redirect_uri={KAKAO_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=profile_nickname,account_email,talk_message"
        f"&state={state}"
    )

    # Store state in session (simplified - using cookie)
    response = RedirectResponse(url=auth_url, status_code=302)
    response.set_cookie(
        key="oauth_state",
        value=state,
        max_age=600,  # 10 minutes
        httponly=True
    )
    return response


@router.get("/kakao/callback")
async def kakao_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None
):
    """
    Step 2: Handle Kakao OAuth callback
    Exchange authorization code for access token
    """
    # Check for errors from Kakao
    if error:
        return HTMLResponse(
            content=get_html_response(
                "Login Failed",
                f"Kakao login error: {error_description or error}",
                "/",
                is_error=True
            ),
            status_code=400
        )

    if not code:
        return HTMLResponse(
            content=get_html_response(
                "Login Failed",
                "No authorization code received",
                "/",
                is_error=True
            ),
            status_code=400
        )

    # Verify state (CSRF protection)
    stored_state = request.cookies.get("oauth_state")
    if state and stored_state and state != stored_state:
        return HTMLResponse(
            content=get_html_response(
                "Security Error",
                "State mismatch - possible CSRF attack",
                "/",
                is_error=True
            ),
            status_code=400
        )

    # Exchange code for access token
    try:
        token_data_request = {
            "grant_type": "authorization_code",
            "client_id": KAKAO_CLIENT_ID,
            "redirect_uri": KAKAO_REDIRECT_URI,
            "code": code,
        }
        # Add client_secret if configured
        if KAKAO_CLIENT_SECRET:
            token_data_request["client_secret"] = KAKAO_CLIENT_SECRET

        token_response = requests.post(
            KAKAO_TOKEN_URL,
            data=token_data_request,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )

        if token_response.status_code != 200:
            error_data = token_response.json()
            error_msg = error_data.get('error_description') or error_data.get('error', 'Unknown error')
            print(f"[Kakao Token Error] {error_data}")  # Debug log
            return HTMLResponse(
                content=get_html_response(
                    "Token Error",
                    f"Failed to get access token: {error_msg}",
                    "/",
                    is_error=True
                ),
                status_code=400
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 21600)

    except requests.RequestException as e:
        return HTMLResponse(
            content=get_html_response(
                "Network Error",
                f"Failed to connect to Kakao: {str(e)}",
                "/",
                is_error=True
            ),
            status_code=500
        )

    # Get user info from Kakao
    try:
        user_response = requests.get(
            KAKAO_USER_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )

        if user_response.status_code != 200:
            return HTMLResponse(
                content=get_html_response(
                    "User Info Error",
                    "Failed to get user information from Kakao",
                    "/",
                    is_error=True
                ),
                status_code=400
            )

        user_data = user_response.json()
        kakao_id = str(user_data.get("id"))
        properties = user_data.get("properties", {})
        kakao_account = user_data.get("kakao_account", {})

        nickname = properties.get("nickname", f"User_{kakao_id[:8]}")
        profile_image = properties.get("profile_image")
        email = kakao_account.get("email")

    except requests.RequestException as e:
        return HTMLResponse(
            content=get_html_response(
                "Network Error",
                f"Failed to get user info: {str(e)}",
                "/",
                is_error=True
            ),
            status_code=500
        )

    # Save user to database
    from server.users import UserService
    print(f"[Debug] Saving user: kakao_id={kakao_id}, nickname={nickname}")

    try:
        user_service = UserService()
        user = user_service.upsert_user(
            kakao_id=kakao_id,
            nickname=nickname,
            email=email,
            profile_image=profile_image,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=datetime.now() + timedelta(seconds=expires_in)
        )
        print(f"[Debug] User save result: {user}")
    except Exception as e:
        print(f"[Debug] Database error: {e}")
        import traceback
        traceback.print_exc()
        user = None

    if not user:
        return HTMLResponse(
            content=get_html_response(
                "Database Error",
                "Failed to save user information",
                "/",
                is_error=True
            ),
            status_code=500
        )

    # Create session
    session_token = user_service.create_session(kakao_id)

    # Redirect to dashboard with session cookie
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="session_token",
        value=session_token,
        max_age=86400 * 7,  # 7 days
        httponly=True,
        samesite="lax"
    )
    response.delete_cookie("oauth_state")

    return response


@router.get("/logout")
async def logout(request: Request):
    """
    Logout user and clear session
    """
    session_token = request.cookies.get("session_token")

    if session_token:
        from server.users import UserService
        user_service = UserService()
        user_service.delete_session(session_token)

    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("session_token")

    return response


@router.get("/me")
async def get_current_user(request: Request):
    """
    Get current logged-in user info (API endpoint)
    """
    session_token = request.cookies.get("session_token")

    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    from server.users import UserService
    user_service = UserService()
    user = user_service.get_user_by_session(session_token)

    if not user:
        raise HTTPException(status_code=401, detail="Session expired")

    # Remove sensitive fields
    safe_user = {
        "kakao_id": user.get("kakao_id"),
        "nickname": user.get("nickname"),
        "email": user.get("email"),
        "profile_image": user.get("profile_image"),
        "current_level": user.get("current_level", 3),
        "current_score_level": user.get("current_score_level", 3),
        "created_at": user.get("created_at"),
    }

    return {"user": safe_user}


@router.post("/refresh")
async def refresh_token(request: Request):
    """
    Refresh Kakao access token
    """
    session_token = request.cookies.get("session_token")

    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    from server.users import UserService
    user_service = UserService()
    user = user_service.get_user_by_session(session_token)

    if not user:
        raise HTTPException(status_code=401, detail="Session expired")

    refresh_token = user.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="No refresh token available")

    # Refresh token with Kakao
    try:
        response = requests.post(
            KAKAO_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": KAKAO_CLIENT_ID,
                "refresh_token": refresh_token,
            },
            timeout=10
        )

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to refresh token")

        token_data = response.json()
        new_access_token = token_data.get("access_token")
        new_refresh_token = token_data.get("refresh_token", refresh_token)
        expires_in = token_data.get("expires_in", 21600)

        # Update user tokens
        user_service.update_tokens(
            kakao_id=user.get("kakao_id"),
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_expires_at=datetime.now() + timedelta(seconds=expires_in)
        )

        return {"message": "Token refreshed successfully"}

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
