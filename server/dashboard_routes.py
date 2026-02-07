"""
Analytics Dashboard Routes
Provides API endpoints and HTML dashboard for system analytics.
"""

from datetime import date, datetime, timedelta
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

from src.supabase_service import SupabaseService

router = APIRouter()


def _require_auth(request: Request):
    """Require authenticated session for dashboard endpoints"""
    from server.users import UserService
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = UserService().get_user_by_session(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired")
    return user


def get_dashboard_stats() -> dict:
    """Gather all dashboard statistics from the database"""
    supabase = SupabaseService()
    stats = {}

    # 1. Problem stats
    problems = supabase.client.table("problems").select(
        "problem_id, year, exam, status, score, score_verified, "
        "answer_verified, problem_image_url, difficulty, subject, unit"
    ).execute()

    all_problems = problems.data
    stats["total_problems"] = len(all_problems)
    stats["ready_problems"] = sum(1 for p in all_problems if p["status"] == "ready")
    stats["with_images"] = sum(1 for p in all_problems if p.get("problem_image_url"))
    stats["with_verified_answers"] = sum(1 for p in all_problems if p.get("answer_verified"))

    # By year/exam breakdown
    year_exam = {}
    for p in all_problems:
        key = f"{p['year']}_{p['exam']}"
        if key not in year_exam:
            year_exam[key] = {"total": 0, "ready": 0, "images": 0, "verified": 0}
        year_exam[key]["total"] += 1
        if p["status"] == "ready":
            year_exam[key]["ready"] += 1
        if p.get("problem_image_url"):
            year_exam[key]["images"] += 1
        if p.get("answer_verified"):
            year_exam[key]["verified"] += 1
    stats["by_year_exam"] = year_exam

    # By unit breakdown
    unit_counts = {}
    for p in all_problems:
        unit = p.get("unit") or "unclassified"
        unit_counts[unit] = unit_counts.get(unit, 0) + 1
    stats["by_unit"] = unit_counts

    # 2. Hint stats
    hints = supabase.client.table("hints").select("problem_id, stage", count="exact").execute()
    stats["total_hints"] = hints.count if hints.count else len(hints.data)
    stats["hints_per_stage"] = {}
    for h in hints.data:
        stage = h["stage"]
        stats["hints_per_stage"][stage] = stats["hints_per_stage"].get(stage, 0) + 1

    # 3. User stats
    users = supabase.client.table("users").select(
        "id, nickname, current_level, current_score_level, "
        "total_problems_solved, correct_count, consecutive_correct, consecutive_wrong"
    ).execute()

    stats["total_users"] = len(users.data)
    stats["users"] = []
    for u in users.data:
        solved = u.get("total_problems_solved", 0) or 0
        correct = u.get("correct_count", 0) or 0
        rate = round(100 * correct / solved, 1) if solved > 0 else 0
        stats["users"].append({
            "nickname": u.get("nickname", "?"),
            "level": u.get("current_level", 3),
            "score_level": u.get("current_score_level", 3),
            "solved": solved,
            "correct": correct,
            "correct_rate": rate,
            "streak_correct": u.get("consecutive_correct", 0) or 0,
            "streak_wrong": u.get("consecutive_wrong", 0) or 0,
        })

    # 4. Delivery stats
    deliveries = supabase.client.table("deliveries").select(
        "id, problem_id, status, is_correct, delivered_at, "
        "hint_1_viewed_at, hint_2_viewed_at, hint_3_viewed_at"
    ).execute()

    all_deliveries = deliveries.data
    stats["total_deliveries"] = len(all_deliveries)
    stats["answered"] = sum(1 for d in all_deliveries if d.get("is_correct") is not None)
    stats["correct_answers"] = sum(1 for d in all_deliveries if d.get("is_correct") is True)
    stats["wrong_answers"] = sum(1 for d in all_deliveries if d.get("is_correct") is False)
    stats["hint_usage"] = {
        "hint_1": sum(1 for d in all_deliveries if d.get("hint_1_viewed_at")),
        "hint_2": sum(1 for d in all_deliveries if d.get("hint_2_viewed_at")),
        "hint_3": sum(1 for d in all_deliveries if d.get("hint_3_viewed_at")),
    }

    # 5. Schedule stats (today)
    today = date.today().isoformat()
    schedules = supabase.client.table("daily_schedules").select(
        "status, problem_id"
    ).eq("scheduled_date", today).execute()

    stats["today_schedules"] = {
        "total": len(schedules.data),
        "scheduled": sum(1 for s in schedules.data if s["status"] == "scheduled"),
        "sent": sum(1 for s in schedules.data if s["status"] == "sent"),
        "failed": sum(1 for s in schedules.data if s["status"] == "failed"),
    }

    return stats


@router.get("/api")
async def dashboard_api(request: Request):
    """JSON API for dashboard statistics (requires auth)"""
    _require_auth(request)
    return get_dashboard_stats()


@router.get("", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """HTML dashboard page (requires auth)"""
    _require_auth(request)
    stats = get_dashboard_stats()

    # Build year/exam table rows
    year_exam_rows = ""
    for key, val in sorted(stats["by_year_exam"].items(), reverse=True):
        year_exam_rows += f"""
        <tr>
            <td>{key}</td>
            <td>{val['total']}</td>
            <td>{val['ready']}</td>
            <td>{val['images']}</td>
            <td>{val['verified']}</td>
        </tr>"""

    # Build unit breakdown rows
    unit_rows = ""
    for unit, count in sorted(stats["by_unit"].items(), key=lambda x: -x[1]):
        unit_rows += f"<tr><td>{unit}</td><td>{count}</td></tr>"

    # Build user rows
    user_rows = ""
    for u in stats["users"]:
        rate_color = "#059669" if u["correct_rate"] >= 70 else "#d97706" if u["correct_rate"] >= 40 else "#dc2626"
        user_rows += f"""
        <tr>
            <td>{u['nickname']}</td>
            <td>Lv.{u['level']}</td>
            <td>{u['score_level']}pt</td>
            <td>{u['solved']}</td>
            <td style="color:{rate_color};font-weight:bold">{u['correct_rate']}%</td>
            <td>{u['streak_correct']}</td>
            <td>{u['streak_wrong']}</td>
        </tr>"""

    overall_rate = round(100 * stats["correct_answers"] / stats["answered"], 1) if stats["answered"] > 0 else 0
    today = stats["today_schedules"]

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>수능 수학 - 분석 대시보드</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:#f1f5f9; color:#1e293b; }}
        .header {{ background:linear-gradient(135deg,#1e40af,#4f46e5); color:white; padding:24px 32px; }}
        .header h1 {{ font-size:24px; margin-bottom:4px; }}
        .header p {{ opacity:0.8; font-size:14px; }}
        .container {{ max-width:1200px; margin:0 auto; padding:24px; }}
        .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px; margin-bottom:24px; }}
        .card {{ background:white; border-radius:12px; padding:20px; box-shadow:0 1px 3px rgba(0,0,0,0.1); }}
        .card h3 {{ font-size:13px; color:#64748b; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:8px; }}
        .card .value {{ font-size:32px; font-weight:700; color:#1e293b; }}
        .card .sub {{ font-size:13px; color:#94a3b8; margin-top:4px; }}
        .section {{ background:white; border-radius:12px; padding:24px; box-shadow:0 1px 3px rgba(0,0,0,0.1); margin-bottom:24px; }}
        .section h2 {{ font-size:18px; margin-bottom:16px; color:#1e293b; border-bottom:2px solid #e2e8f0; padding-bottom:8px; }}
        table {{ width:100%; border-collapse:collapse; font-size:14px; }}
        th {{ background:#f8fafc; padding:10px 12px; text-align:left; font-weight:600; color:#475569; border-bottom:2px solid #e2e8f0; }}
        td {{ padding:10px 12px; border-bottom:1px solid #f1f5f9; }}
        tr:hover {{ background:#f8fafc; }}
        .badge {{ display:inline-block; padding:2px 8px; border-radius:9999px; font-size:12px; font-weight:600; }}
        .badge-green {{ background:#dcfce7; color:#166534; }}
        .badge-yellow {{ background:#fef9c3; color:#854d0e; }}
        .badge-red {{ background:#fee2e2; color:#991b1b; }}
        .back-link {{ display:inline-block; margin-top:16px; color:#6366f1; text-decoration:none; font-size:14px; }}
        .back-link:hover {{ text-decoration:underline; }}
        .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:24px; }}
        @media(max-width:768px) {{ .two-col {{ grid-template-columns:1fr; }} }}
    </style>
</head>
<body>
    <div class="header">
        <h1>수능 수학 분석</h1>
        <p>시스템 대시보드 - {date.today().isoformat()}</p>
    </div>
    <div class="container">
        <!-- Summary Cards -->
        <div class="grid">
            <div class="card">
                <h3>전체 문제</h3>
                <div class="value">{stats['total_problems']}</div>
                <div class="sub">{stats['ready_problems']}개 준비 / {stats['with_images']}개 이미지</div>
            </div>
            <div class="card">
                <h3>검증된 정답</h3>
                <div class="value">{stats['with_verified_answers']}</div>
                <div class="sub">{round(100*stats['with_verified_answers']/max(stats['total_problems'],1))}% 완료</div>
            </div>
            <div class="card">
                <h3>힌트 수</h3>
                <div class="value">{stats['total_hints']}</div>
                <div class="sub">1단계: {stats['hints_per_stage'].get(1,0)} / 2단계: {stats['hints_per_stage'].get(2,0)} / 3단계: {stats['hints_per_stage'].get(3,0)}</div>
            </div>
            <div class="card">
                <h3>사용자</h3>
                <div class="value">{stats['total_users']}</div>
                <div class="sub">총 {stats['total_deliveries']}회 발송</div>
            </div>
            <div class="card">
                <h3>전체 정답률</h3>
                <div class="value" style="color:{'#059669' if overall_rate >= 60 else '#d97706'}">{overall_rate}%</div>
                <div class="sub">{stats['correct_answers']}/{stats['answered']}회 응답</div>
            </div>
            <div class="card">
                <h3>오늘 스케줄</h3>
                <div class="value">{today['total']}</div>
                <div class="sub">
                    <span class="badge badge-green">{today['sent']}건 발송</span>
                    <span class="badge badge-yellow">{today['scheduled']}건 대기</span>
                    <span class="badge badge-red">{today['failed']}건 실패</span>
                </div>
            </div>
        </div>

        <div class="two-col">
            <!-- Problems by Year/Exam -->
            <div class="section">
                <h2>연도/시험별 문제</h2>
                <table>
                    <thead><tr><th>연도_시험</th><th>전체</th><th>준비</th><th>이미지</th><th>검증</th></tr></thead>
                    <tbody>{year_exam_rows}</tbody>
                </table>
            </div>

            <!-- Problems by Unit -->
            <div class="section">
                <h2>단원별 문제</h2>
                <table>
                    <thead><tr><th>단원</th><th>문제 수</th></tr></thead>
                    <tbody>{unit_rows}</tbody>
                </table>
            </div>
        </div>

        <!-- User Stats -->
        <div class="section">
            <h2>사용자 성과</h2>
            <table>
                <thead><tr><th>닉네임</th><th>레벨</th><th>점수</th><th>풀이</th><th>정답률</th><th>연속+</th><th>연속-</th></tr></thead>
                <tbody>{user_rows if user_rows else '<tr><td colspan="7" style="text-align:center;color:#94a3b8">아직 사용자가 없습니다</td></tr>'}</tbody>
            </table>
        </div>

        <!-- Hint Usage -->
        <div class="section">
            <h2>힌트 사용 현황</h2>
            <div class="grid" style="grid-template-columns:repeat(3,1fr)">
                <div class="card">
                    <h3>1단계 (개념 방향)</h3>
                    <div class="value">{stats['hint_usage']['hint_1']}</div>
                </div>
                <div class="card">
                    <h3>2단계 (핵심 변환)</h3>
                    <div class="value">{stats['hint_usage']['hint_2']}</div>
                </div>
                <div class="card">
                    <h3>3단계 (결정적 한 줄)</h3>
                    <div class="value">{stats['hint_usage']['hint_3']}</div>
                </div>
            </div>
        </div>

        <a href="/dashboard" class="back-link">&larr; 대시보드로 돌아가기</a>
    </div>
</body>
</html>"""

    return HTMLResponse(content=html)
