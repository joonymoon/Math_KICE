"""
FastAPI Main Application
KICE Math KakaoTalk Service Web Server
"""

import os
import sys
import io
from pathlib import Path
from contextlib import asynccontextmanager

# Force UTF-8 encoding for stdout/stderr to avoid cp949 codec errors with emojis
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from server.auth import router as auth_router
from server.message_routes import router as message_router
from server.problem_routes import router as problem_router
from server.card_routes import router as card_router
from server.scheduler import scheduler_router
from server.dashboard_routes import router as dashboard_analytics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    print("=" * 50)
    print("KICE Math KakaoTalk Service - Server Starting")
    print("=" * 50)
    yield
    print("Server shutting down...")


app = FastAPI(
    title="KICE Math KakaoTalk Service",
    description="Daily math problems via KakaoTalk",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(message_router, prefix="/message", tags=["Message"])
app.include_router(problem_router, prefix="/problem", tags=["Problem"])
app.include_router(card_router, tags=["Card"])
app.include_router(scheduler_router, prefix="/schedule", tags=["Scheduler"])
app.include_router(dashboard_analytics_router, prefix="/analytics", tags=["Analytics"])

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Simple HTML templates (inline for simplicity)
def get_html_template(title: str, content: str) -> str:
    """Generate simple HTML page"""
    return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - KICE Math</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
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
            width: 90%;
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }}
        .subtitle {{
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }}
        .kakao-btn {{
            display: inline-block;
            background: #FEE500;
            color: #000;
            padding: 15px 40px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: bold;
            font-size: 16px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .kakao-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(254, 229, 0, 0.4);
        }}
        .kakao-icon {{
            margin-right: 8px;
        }}
        .features {{
            margin-top: 30px;
            text-align: left;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }}
        .features h3 {{
            color: #333;
            margin-bottom: 15px;
            font-size: 16px;
        }}
        .features ul {{
            list-style: none;
        }}
        .features li {{
            padding: 8px 0;
            color: #555;
            font-size: 14px;
        }}
        .features li:before {{
            content: "\2713 ";
            color: #4f46e5;
            font-weight: bold;
            margin-right: 8px;
        }}
        .user-info {{
            background: #e8f5e9;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .user-info h2 {{
            color: #2e7d32;
            margin-bottom: 10px;
        }}
        .user-info p {{
            color: #555;
            margin: 5px 0;
        }}
        .logout-btn {{
            display: inline-block;
            background: #ff5252;
            color: white;
            padding: 10px 30px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            margin-top: 15px;
        }}
        .error {{
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .success {{
            background: #e8f5e9;
            color: #2e7d32;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with login button"""
    content = """
        <h1>수능 수학 매일 풀기</h1>
        <p class="subtitle">카카오톡으로 매일 수능 수학 문제를 받아보세요</p>

        <a href="/auth/kakao" class="kakao-btn">
            <span class="kakao-icon">K</span>
            카카오 로그인
        </a>

        <div class="features">
            <h3>서비스 기능</h3>
            <ul>
                <li>매일 카카오톡으로 수능 수학 문제 발송</li>
                <li>단계별 힌트 제공 (3단계)</li>
                <li>상세한 풀이와 해설</li>
                <li>나의 수준에 맞는 적응형 난이도</li>
            </ul>
        </div>
    """
    return get_html_template("홈", content)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """User dashboard (requires login)"""
    # Check session cookie
    session_token = request.cookies.get("session_token")

    if not session_token:
        return RedirectResponse(url="/?error=login_required", status_code=302)

    # Get user info from session
    from server.users import UserService
    user_service = UserService()
    user = user_service.get_user_by_session(session_token)

    if not user:
        response = RedirectResponse(url="/?error=session_expired", status_code=302)
        response.delete_cookie("session_token")
        return response

    nickname = user.get('nickname', '사용자')
    level = user.get('current_level', 3)
    score_level = user.get('current_score_level', 3)
    solved = user.get('total_problems_solved', 0) or 0
    correct = user.get('correct_count', 0) or 0
    rate = round(100 * correct / solved, 1) if solved > 0 else 0
    streak_c = user.get('consecutive_correct', 0) or 0
    joined = str(user.get('created_at', ''))[:10]

    # H2: Rich dashboard with stats
    content = f"""
        <div class="user-info">
            <h2>{nickname}님, 안녕하세요!</h2>
            <p style="font-size:13px; color:#666; margin-top:4px;">가입일: {joined}</p>
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin:15px 0; text-align:center;">
            <div style="background:#f0f4ff; padding:12px; border-radius:10px;">
                <div style="font-size:24px; font-weight:700; color:#4f46e5;">Lv.{level}</div>
                <div style="font-size:12px; color:#6b7280;">난이도 레벨</div>
            </div>
            <div style="background:#f0fdf4; padding:12px; border-radius:10px;">
                <div style="font-size:24px; font-weight:700; color:#059669;">{rate}%</div>
                <div style="font-size:12px; color:#6b7280;">정답률</div>
            </div>
            <div style="background:#fefce8; padding:12px; border-radius:10px;">
                <div style="font-size:24px; font-weight:700; color:#b45309;">{solved}</div>
                <div style="font-size:12px; color:#6b7280;">풀이 수</div>
            </div>
            <div style="background:#fdf2f8; padding:12px; border-radius:10px;">
                <div style="font-size:24px; font-weight:700; color:#db2777;">{streak_c}</div>
                <div style="font-size:12px; color:#6b7280;">연속 정답</div>
            </div>
        </div>

        <div style="margin: 20px 0;">
            <a href="/problem/admin" class="kakao-btn" style="display: inline-block; margin: 5px; background: #4f46e5; color: white;">문제 관리</a>
            <a href="/card-maker" class="kakao-btn" style="display: inline-block; margin: 5px; background: #059669; color: white;">카드 제작</a>
            <a href="/analytics" class="kakao-btn" style="display: inline-block; margin: 5px; background: #7c3aed; color: white;">분석</a>
            <a href="/message/test-page" class="kakao-btn" style="display: inline-block; margin: 5px;">메시지 테스트</a>
        </div>

        <a href="/auth/logout" class="logout-btn">로그아웃</a>
    """
    return get_html_template("대시보드", content)


@app.get("/card-maker", response_class=HTMLResponse)
async def card_maker():
    """Card maker UI"""
    with open(Path(__file__).parent / "static" / "simple-crop.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "KICE Math KakaoTalk"}


# No custom error handlers - FastAPI's default returns JSON for all errors


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
