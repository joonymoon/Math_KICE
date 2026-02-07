"""
Message API Routes
Send KakaoTalk messages to users
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from server.users import UserService
from server.kakao_message import KakaoMessageService

router = APIRouter()
message_service = KakaoMessageService()


class SendMessageRequest(BaseModel):
    text: str
    button_title: Optional[str] = None
    button_url: Optional[str] = None


@router.post("/send-test")
async def send_test_message(request: Request):
    """
    Send test message to logged-in user
    """
    session_token = request.cookies.get("session_token")

    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_service = UserService()
    user = user_service.get_user_by_session(session_token)

    if not user:
        raise HTTPException(status_code=401, detail="Session expired")

    access_token = user.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token")

    # Send test message (버튼 없음 - localhost URL은 모바일에서 동작하지 않음)
    result = message_service.send_text_to_me(
        access_token=access_token,
        text="KICE Math 테스트 메시지입니다!\n\n카카오톡 연동이 성공적으로 완료되었습니다."
    )

    if result.get("success"):
        return {"message": "Test message sent successfully", "result": result}
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to send message: {result.get('error')}"
        )


@router.post("/send")
async def send_message(request: Request, body: SendMessageRequest):
    """
    Send custom message to logged-in user
    """
    session_token = request.cookies.get("session_token")

    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_service = UserService()
    user = user_service.get_user_by_session(session_token)

    if not user:
        raise HTTPException(status_code=401, detail="Session expired")

    access_token = user.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token")

    result = message_service.send_text_to_me(
        access_token=access_token,
        text=body.text,
        button_title=body.button_title,
        button_url=body.button_url
    )

    if result.get("success"):
        return {"message": "Message sent successfully", "result": result}
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to send message: {result.get('error')}"
        )


@router.get("/test-page", response_class=HTMLResponse)
async def message_test_page(request: Request):
    """
    Test page for sending messages
    """
    session_token = request.cookies.get("session_token")

    if not session_token:
        return HTMLResponse(
            content="<h1>Login required</h1><a href='/'>Go to login</a>",
            status_code=401
        )

    user_service = UserService()
    user = user_service.get_user_by_session(session_token)

    if not user:
        return HTMLResponse(
            content="<h1>Session expired</h1><a href='/'>Go to login</a>",
            status_code=401
        )

    html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Message Test - KICE Math</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 500px;
            width: 90%;
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        .user-info {{
            background: #e8f5e9;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .btn {{
            display: inline-block;
            background: #FEE500;
            color: #000;
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            margin: 5px;
        }}
        .btn:hover {{
            background: #e6cf00;
        }}
        .btn-purple {{
            background: #667eea;
            color: white;
        }}
        .btn-purple:hover {{
            background: #5a6fd6;
        }}
        .result {{
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
            display: none;
        }}
        .result.success {{
            background: #e8f5e9;
            color: #2e7d32;
        }}
        .result.error {{
            background: #ffebee;
            color: #c62828;
        }}
        textarea {{
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin-bottom: 10px;
            font-size: 14px;
            resize: vertical;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>KakaoTalk Message Test</h1>

        <div class="user-info">
            <p><strong>Nickname:</strong> {user.get('nickname', 'N/A')}</p>
            <p><strong>Email:</strong> {user.get('email', 'N/A')}</p>
        </div>

        <h3>1. Send Test Message</h3>
        <button class="btn" onclick="sendTest()">Send Test Message</button>

        <h3 style="margin-top: 30px;">2. Send Custom Message</h3>
        <textarea id="customMessage" rows="4" placeholder="Enter your message here..."></textarea>
        <button class="btn btn-purple" onclick="sendCustom()">Send Custom Message</button>

        <div id="result" class="result"></div>

        <p style="margin-top: 30px;">
            <a href="/dashboard">Back to Dashboard</a> |
            <a href="/auth/logout">Logout</a>
        </p>
    </div>

    <script>
        async function sendTest() {{
            const resultDiv = document.getElementById('result');
            resultDiv.style.display = 'block';
            resultDiv.className = 'result';
            resultDiv.innerText = 'Sending...';

            try {{
                const response = await fetch('/message/send-test', {{
                    method: 'POST',
                    credentials: 'include'
                }});

                const data = await response.json();

                if (response.ok) {{
                    resultDiv.className = 'result success';
                    resultDiv.innerText = 'Message sent! Check your KakaoTalk.';
                }} else {{
                    resultDiv.className = 'result error';
                    resultDiv.innerText = 'Error: ' + (data.detail || 'Unknown error');
                }}
            }} catch (e) {{
                resultDiv.className = 'result error';
                resultDiv.innerText = 'Network error: ' + e.message;
            }}
        }}

        async function sendCustom() {{
            const text = document.getElementById('customMessage').value;
            if (!text.trim()) {{
                alert('Please enter a message');
                return;
            }}

            const resultDiv = document.getElementById('result');
            resultDiv.style.display = 'block';
            resultDiv.className = 'result';
            resultDiv.innerText = 'Sending...';

            try {{
                const response = await fetch('/message/send', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    credentials: 'include',
                    body: JSON.stringify({{ text: text }})
                }});

                const data = await response.json();

                if (response.ok) {{
                    resultDiv.className = 'result success';
                    resultDiv.innerText = 'Message sent! Check your KakaoTalk.';
                }} else {{
                    resultDiv.className = 'result error';
                    resultDiv.innerText = 'Error: ' + (data.detail || 'Unknown error');
                }}
            }} catch (e) {{
                resultDiv.className = 'result error';
                resultDiv.innerText = 'Network error: ' + e.message;
            }}
        }}
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html)
