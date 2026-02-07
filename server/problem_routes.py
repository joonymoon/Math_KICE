"""
Problem API Routes
Manage and send math problems via KakaoTalk
"""

from fastapi import APIRouter, Request, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from server.users import UserService
from server.kakao_message import KakaoMessageService
from src.supabase_service import SupabaseService
from server.card_image_generator import CardImageGenerator

router = APIRouter()
message_service = KakaoMessageService()
# Fixed: CardImageGenerator import moved to top of file


class SendProblemRequest(BaseModel):
    problem_id: str


class BulkSendRequest(BaseModel):
    problem_ids: list[str]


class SendBulkRequest(BaseModel):
    problem_ids: List[str]


def get_user_from_session(request: Request):
    """Get authenticated user from session"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_service = UserService()
    user = user_service.get_user_by_session(session_token)

    if not user:
        raise HTTPException(status_code=401, detail="Session expired")

    return user


# ===========================================
# Problem List APIs
# ===========================================

@router.get("/list")
async def list_problems(
    request: Request,
    status: Optional[str] = None,
    year: Optional[int] = None,
    exam: Optional[str] = None,
    score: Optional[int] = None,
    limit: int = 50
):
    """
    Get problem list with filters
    """
    user = get_user_from_session(request)

    try:
        supabase = SupabaseService()
        problems = supabase.get_problems_by_filter(
            status=status,
            year=year,
            exam=exam,
            score=score,
            limit=limit
        )
        return {"problems": problems, "count": len(problems)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ready")
async def get_ready_problems(request: Request):
    """
    Get problems ready to send
    """
    user = get_user_from_session(request)

    try:
        supabase = SupabaseService()
        problems = supabase.get_ready_problems()
        return {"problems": problems, "count": len(problems)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_problem_stats(request: Request):
    """
    Get problem statistics
    """
    user = get_user_from_session(request)

    try:
        supabase = SupabaseService()
        stats = supabase.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin")
async def admin_dashboard(request: Request):
    """
    Admin dashboard for problem management
    """
    user = get_user_from_session(request)

    html = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <title>Problem Admin v2 - KICE Math</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #1e40af 0%, #4f46e5 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .container {
            max-width: 1200px;
            margin: 20px auto;
            padding: 20px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-card h3 { color: #4f46e5; font-size: 32px; }
        .stat-card p { color: #666; margin-top: 5px; }
        .problem-table {
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #4f46e5; color: white; }
        tr:hover { background: #f8f9fa; }
        .status-badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
        .status-ready { background: #e8f5e9; color: #2e7d32; }
        .status-needs_review { background: #fff3e0; color: #ef6c00; }
        .status-sent { background: #e3f2fd; color: #1565c0; }
        .btn { padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; margin: 2px; }
        .btn-send { background: #FEE500; color: #000; }
        .btn-send:hover { background: #e6cf00; }
        .btn-view { background: #4f46e5; color: white; }
        .btn-view:hover { background: #4338ca; }
        .filter-bar { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }
        .filter-bar .filter-row { display: flex; gap: 15px; flex-wrap: wrap; align-items: center; margin-bottom: 10px; }
        .filter-bar .filter-hint { font-size: 12px; color: #666; margin-top: 8px; }
        .filter-bar select { padding: 8px 12px; border: 1px solid #ddd; border-radius: 5px; min-width: 120px; }
        .filter-bar label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; font-weight: 600; color: #444; }
        .nav-links { margin-top: 10px; }
        .nav-links a { color: white; margin: 0 10px; text-decoration: none; }
        .nav-links a:hover { text-decoration: underline; }
        .loading { text-align: center; padding: 40px; color: #666; }
        .result-message { padding: 15px; margin-bottom: 20px; border-radius: 10px; display: none; }
        .result-success { background: #e8f5e9; color: #2e7d32; }
        .result-error { background: #ffebee; color: #c62828; }
        .btn-crop { background: #10B981; color: white; margin-left: 4px; }
        .btn-crop:hover { background: #059669; }

        /* Progress bars */
        .progress-section { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); margin-bottom: 20px; }
        .progress-section h3 { font-size: 15px; color: #333; margin-bottom: 14px; }
        .progress-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
        .progress-label { min-width: 50px; font-size: 13px; font-weight: 600; color: #555; }
        .progress-bar-bg { flex: 1; height: 22px; background: #f0f0f0; border-radius: 11px; overflow: hidden; position: relative; }
        .progress-bar-fill { height: 100%; border-radius: 11px; transition: width 0.6s ease; }
        .progress-bar-fill.done { background: linear-gradient(90deg, #10B981, #34D399); }
        .progress-bar-fill.review { background: linear-gradient(90deg, #F59E0B, #FBBF24); }
        .progress-text { min-width: 80px; font-size: 12px; color: #888; text-align: right; }

        /* Thumbnail */
        .thumb { width: 40px; height: 40px; object-fit: cover; border-radius: 4px; border: 1px solid #eee; cursor: pointer; }
        .thumb:hover { transform: scale(3); position: relative; z-index: 10; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }

        /* Crop Modal Styles */
        .crop-modal-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.7);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.2s;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        .crop-modal-dialog {
            background: white;
            border-radius: 16px;
            width: 95%;
            max-width: 1200px;
            max-height: 95vh;
            overflow: auto;
            box-shadow: 0 25px 50px rgba(0,0,0,0.5);
            padding: 24px;
            animation: slideUp 0.3s;
        }
        @keyframes slideUp {
            from { transform: translateY(50px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        .crop-modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .crop-modal-close {
            background: none;
            border: none;
            font-size: 32px;
            cursor: pointer;
            color: #666;
            line-height: 1;
            padding: 0;
            width: 32px;
            height: 32px;
        }
        .crop-modal-close:hover {
            color: #000;
        }

        /* C1: Mobile responsive */
        @media (max-width: 768px) {
            .header { padding: 12px; }
            .header h1 { font-size: 18px; }
            .container { padding: 10px; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; }
            .stat-card { padding: 12px; }
            .stat-card h3 { font-size: 22px; }
            .problem-table { overflow-x: auto; -webkit-overflow-scrolling: touch; }
            table { min-width: 700px; }
            th, td { padding: 8px 10px; font-size: 13px; }
            .filter-bar .filter-row { flex-direction: column; gap: 8px; }
            .filter-bar select, .filter-bar input { width: 100% !important; min-width: unset; }
            .btn { padding: 6px 10px; font-size: 12px; }
            .crop-modal-dialog { width: 98%; padding: 12px; }
            .nav-links a { margin: 0 5px; font-size: 13px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>수학 문제 관리</h1>
        <div class="nav-links">
            <a href="/dashboard">대시보드</a>
            <a href="/message/test-page">메시지 테스트</a>
            <a href="/auth/logout">로그아웃</a>
        </div>
    </div>
    <div class="container">
        <div id="result-message" class="result-message"></div>
        <div class="stats-grid">
            <div class="stat-card"><h3 id="stat-total">-</h3><p>전체 문제</p></div>
            <div class="stat-card"><h3 id="stat-ready">-</h3><p>발송 준비</p></div>
            <div class="stat-card"><h3 id="stat-review">-</h3><p>검토 필요</p></div>
            <div class="stat-card"><h3 id="stat-sent">-</h3><p>발송 완료</p></div>
        </div>
        <div class="progress-section" id="progress-section" style="display:none;">
            <h3>연도별 검수 진행률</h3>
            <div id="progress-bars"></div>
        </div>
        <div class="filter-bar">
            <div class="filter-row">
                <label>검색
                    <input type="text" id="filter-search" placeholder="문제 ID..." style="padding: 8px 12px; border: 1px solid #ddd; border-radius: 5px; width: 180px;" onkeyup="if(event.key==='Enter') loadProblems()" oninput="if(this.value==='') loadProblems()">
                </label>
                <label>연도
                    <select id="filter-year" onchange="loadProblems()">
                        <option value="">전체</option><option value="2026">2026</option><option value="2025">2025</option>
                        <option value="2024">2024</option><option value="2023">2023</option>
                    </select>
                </label>
                <label>시험
                    <select id="filter-exam" onchange="loadProblems()">
                        <option value="">전체</option><option value="CSAT">수능</option>
                        <option value="KICE6">6월 평가원</option><option value="KICE9">9월 평가원</option>
                    </select>
                </label>
                <label>배점
                    <select id="filter-score" onchange="loadProblems()">
                        <option value="">전체</option><option value="2">2점</option>
                        <option value="3">3점</option><option value="4">4점</option>
                    </select>
                </label>
                <label>상태
                    <select id="filter-status" onchange="loadProblems()">
                        <option value="">전체</option><option value="ready">준비</option>
                        <option value="needs_review">검토 필요</option><option value="sent">발송됨</option>
                    </select>
                </label>
                <button class="btn btn-view" onclick="loadProblems()">새로고침</button>
                <button class="btn" onclick="openAddProblemModal()" style="background: #10B981; color: white; margin-left: 10px;">➕ PDF 업로드</button>
            </div>
            <div class="filter-row">
                <button class="btn btn-send" onclick="sendSelectedProblems()">📤 선택 문제 발송</button>
                <span id="selected-count" style="color: #666; font-size: 14px;"></span>
            </div>
            <div class="filter-hint">💡 Tip: <strong>PDF 업로드</strong> 버튼으로 새 문제 추가 | <strong>크롭</strong> 버튼에서 마우스 휠(확대) + 우클릭 드래그(이동) 사용 가능</div>
        </div>
        <div id="add-problem-modal-root"></div>
        <div class="problem-table">
            <table>
                <thead><tr><th><input type="checkbox" id="select-all" onchange="toggleSelectAll()"></th><th>이미지</th><th>문제 ID</th><th>연도</th><th>시험</th><th>번호</th><th>배점</th><th>정답</th><th>상태</th><th>Notion</th><th>관리</th></tr></thead>
                <tbody id="problem-tbody"><tr><td colspan="6" class="loading">Loading...</td></tr></tbody>
            </table>
        </div>
    </div>
    <script>
        async function loadStats() {
            try {
                const res = await fetch('/problem/stats', {credentials:'include'});
                const data = await res.json();
                document.getElementById('stat-total').textContent = data.total || 0;
                document.getElementById('stat-ready').textContent = data.by_status?.ready || 0;
                document.getElementById('stat-review').textContent = data.by_status?.needs_review || 0;
                document.getElementById('stat-sent').textContent = data.by_status?.sent || 0;
                // 연도별 진행률 바
                const yrs = data.by_year_status;
                if (yrs && Object.keys(yrs).length > 0) {
                    const section = document.getElementById('progress-section');
                    const container = document.getElementById('progress-bars');
                    section.style.display = 'block';
                    container.innerHTML = Object.keys(yrs).sort((a,b)=>b-a).map(y => {
                        const s = yrs[y];
                        const done = (s.ready||0) + (s.sent||0);
                        const pct = s.total > 0 ? Math.round(done / s.total * 100) : 0;
                        return '<div class="progress-row"><span class="progress-label">' + y + '</span><div class="progress-bar-bg"><div class="progress-bar-fill done" style="width:' + pct + '%"></div></div><span class="progress-text">' + done + '/' + s.total + ' (' + pct + '%)</span></div>';
                    }).join('');
                }
            } catch(e) { console.error(e); }
        }
        async function loadProblems() {
            const tbody = document.getElementById('problem-tbody');
            tbody.innerHTML = '<tr><td colspan="11" class="loading">Loading...</td></tr>';
            let url = '/problem/list?limit=100';
            const search = document.getElementById('filter-search').value.trim();
            const status = document.getElementById('filter-status').value;
            const year = document.getElementById('filter-year').value;
            const exam = document.getElementById('filter-exam').value;
            const score = document.getElementById('filter-score').value;
            if (status) url += '&status=' + status;
            if (year) url += '&year=' + year;
            if (exam) url += '&exam=' + exam;
            if (score) url += '&score=' + score;
            try {
                const res = await fetch(url, {credentials:'include'});
                const data = await res.json();
                let problems = data.problems || [];

                // Client-side search filter
                if (search) {
                    problems = problems.filter(p =>
                        p.problem_id.toLowerCase().includes(search.toLowerCase())
                    );
                }

                if (problems.length > 0) {
                    const notionUrl = (pid) => pid ? 'https://notion.so/' + pid.replace(/-/g, '') : '';
                    const thumbHtml = (url) => url ? '<img src="'+url+'" class="thumb" onerror="this.style.display=\\'none\\'">' : '<span style="color:#ccc;font-size:11px;">-</span>';
                    tbody.innerHTML = problems.map(p => '<tr><td><input type="checkbox" class="problem-checkbox" value="'+p.problem_id+'" onchange="updateSelectedCount()"></td><td>'+thumbHtml(p.problem_image_url)+'</td><td>'+p.problem_id+'</td><td>'+(p.year||'-')+'</td><td>'+(p.exam||'-')+'</td><td>'+(p.question_no||'-')+'</td><td>'+(p.score||'-')+'점</td><td>'+(p.answer||'-')+'</td><td><span class="status-badge status-'+p.status+'">'+p.status+'</span></td><td>'+(p.notion_page_id ? '<a href="'+notionUrl(p.notion_page_id)+'" target="_blank" style="color:#2563eb;text-decoration:none;" title="Notion에서 보기">📄</a>' : '-')+'</td><td><button class="btn btn-send" onclick="sendProblem(\\''+p.problem_id+'\\')">발송</button><button class="btn btn-crop" onclick="openCropModal(\\''+p.problem_id+'\\', \\''+( p.problem_image_url||'')+'\\')">크롭</button></td></tr>').join('');
                    updateSelectedCount();
                } else {
                    tbody.innerHTML = '<tr><td colspan="11" class="loading">No problems found</td></tr>';
                }
            } catch(e) { tbody.innerHTML = '<tr><td colspan="11" class="loading">Error</td></tr>'; }
        }
        async function sendProblem(id) {
            // Show preview modal first
            showPreviewModal(id);
        }

        async function sendProblemConfirmed(id) {
            closePreviewModal();
            const msg = document.getElementById('result-message');
            msg.className = 'result-message';
            msg.textContent = '발송 중...';
            msg.style.display = 'block';
            try {
                const res = await fetch('/problem/send', {method:'POST', headers:{'Content-Type':'application/json', 'Accept':'application/json'}, credentials:'include', body:JSON.stringify({problem_id:id})});
                let data;
                const text = await res.text();
                try { data = JSON.parse(text); } catch { data = {detail: text.substring(0, 200)}; }
                msg.className = res.ok ? 'result-message result-success' : 'result-message result-error';
                msg.textContent = res.ok ? 'Sent!' : ('Error: '+(data.detail||'Failed'));
                if(res.ok) { loadProblems(); loadStats(); }
            } catch(e) { msg.className='result-message result-error'; msg.textContent='발송 실패: '+e.message; }
            setTimeout(() => msg.style.display='none', 8000);
        }

        async function showPreviewModal(problemId) {
            // Fetch problem metadata
            try {
                const res = await fetch(`/problem/${problemId}/metadata`, {credentials:'include'});
                const problem = await res.json();

                // Build preview content - use image_url from metadata, fallback to constructed URL
                const cardImageUrl = problem.image_url
                    ? `${problem.image_url}?t=${Date.now()}`
                    : `https://gusahlxqyyqmaalwdtjw.supabase.co/storage/v1/object/public/problem-images-v2/${problemId}.png?t=${Date.now()}`;

                const previewHtml = `
                    <div class="crop-modal-overlay" id="preview-modal" onclick="if(event.target===this) closePreviewModal()">
                        <div class="crop-modal-dialog" style="max-width: 600px;">
                            <div class="crop-modal-header">
                                <h2>📤 발송 미리보기</h2>
                                <button class="crop-modal-close" onclick="closePreviewModal()">&times;</button>
                            </div>
                            <div style="padding: 20px; text-align: center;">
                                <h3 style="margin-bottom: 15px; color: #333;">${problem.year || ''} ${problem.exam || ''} ${problem.question_no || ''}번</h3>
                                <img src="${cardImageUrl}" alt="Card Preview" style="max-width: 100%; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                                <div style="display: none; padding: 40px; background: #f5f5f5; border-radius: 12px; color: #666;">카드 이미지 로드 실패</div>
                                <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 10px; text-align: left;">
                                    <p><strong>난이도:</strong> ${problem.difficulty || '-'}</p>
                                    <p><strong>단원:</strong> ${problem.category || '-'}</p>
                                    <p style="margin-top: 10px; font-size: 13px; color: #666;">이 카드가 카카오톡으로 발송됩니다.</p>
                                </div>
                                <div style="margin-top: 20px; display: flex; gap: 10px; justify-content: center;">
                                    <button onclick="sendProblemConfirmed('${problemId}')" style="padding: 12px 24px; background: #FEE500; color: #000; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 15px;">✓ 확인 및 발송</button>
                                    <button onclick="closePreviewModal()" style="padding: 12px 24px; background: #e0e0e0; color: #333; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 15px;">취소</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;

                document.body.insertAdjacentHTML('beforeend', previewHtml);
            } catch (e) {
                console.error('Preview failed:', e);
                // Fallback to direct send
                sendProblemConfirmed(problemId);
            }
        }

        function closePreviewModal() {
            const modal = document.getElementById('preview-modal');
            if (modal) modal.remove();
        }
        function showSuccessMessage(text) {
            const msg = document.getElementById('result-message');
            msg.className = 'result-message result-success';
            msg.textContent = text;
            msg.style.display = 'block';
            setTimeout(() => msg.style.display='none', 5000);
        }

        let cropModalRoot = null;

        function openCropModal(problemId, imageUrl) {
            if (!cropModalRoot) {
                cropModalRoot = ReactDOM.createRoot(document.getElementById('crop-modal-root'));
            }

            cropModalRoot.render(
                React.createElement(window.CropModal, {
                    problemId: problemId,
                    existingImageUrl: imageUrl,
                    onClose: () => cropModalRoot.render(null),
                    onSuccess: (result) => {
                        cropModalRoot.render(null);
                        loadProblems();
                        loadStats();
                        showSuccessMessage('이미지 업데이트 완료!');
                    }
                })
            );
        }

        function toggleSelectAll() {
            const selectAll = document.getElementById('select-all');
            const checkboxes = document.querySelectorAll('.problem-checkbox');
            checkboxes.forEach(cb => cb.checked = selectAll.checked);
            updateSelectedCount();
        }

        function updateSelectedCount() {
            const checkboxes = document.querySelectorAll('.problem-checkbox:checked');
            const count = checkboxes.length;
            const countSpan = document.getElementById('selected-count');
            if (count > 0) {
                countSpan.textContent = `${count}개 선택됨`;
                countSpan.style.fontWeight = 'bold';
                countSpan.style.color = '#4f46e5';
            } else {
                countSpan.textContent = '';
            }

            // Update select-all checkbox state
            const allCheckboxes = document.querySelectorAll('.problem-checkbox');
            const selectAll = document.getElementById('select-all');
            if (allCheckboxes.length > 0) {
                selectAll.checked = count === allCheckboxes.length;
                selectAll.indeterminate = count > 0 && count < allCheckboxes.length;
            }
        }

        async function sendSelectedProblems() {
            const checkboxes = document.querySelectorAll('.problem-checkbox:checked');
            const problemIds = Array.from(checkboxes).map(cb => cb.value);

            if (problemIds.length === 0) {
                alert('발송할 문제를 선택해주세요.');
                return;
            }

            if (!confirm(`선택한 ${problemIds.length}개의 문제를 발송하시겠습니까?`)) {
                return;
            }

            const msg = document.getElementById('result-message');
            msg.className = 'result-message';
            msg.textContent = `${problemIds.length}개의 문제 발송 중...`;
            msg.style.display = 'block';

            try {
                const res = await fetch('/problem/send-bulk', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ problem_ids: problemIds })
                });

                const data = await res.json();

                if (res.ok) {
                    msg.className = 'result-message result-success';
                    msg.textContent = `성공: ${data.success_count}개, 실패: ${data.failure_count}개`;
                    loadProblems();
                    loadStats();

                    // Clear selection
                    document.getElementById('select-all').checked = false;
                    updateSelectedCount();
                } else {
                    msg.className = 'result-message result-error';
                    msg.textContent = 'Error: ' + (data.detail || 'Failed');
                }
            } catch (e) {
                msg.className = 'result-message result-error';
                msg.textContent = '발송 중 오류 발생: ' + e.message;
            }

            setTimeout(() => msg.style.display = 'none', 5000);
        }

        function openAddProblemModal() {
            console.log('[Modal] Opening add problem modal');
            const modalHtml = `
                <div class="crop-modal-overlay" id="add-problem-modal" onclick="if(event.target===this) closeAddProblemModal()">
                    <div class="crop-modal-dialog" style="max-width: 800px;">
                        <div class="crop-modal-header">
                            <h2>➕ 문제 추가</h2>
                            <button class="crop-modal-close" onclick="closeAddProblemModal()">&times;</button>
                        </div>
                        <div style="padding: 24px;">
                            <!-- Tab buttons - 큰 버튼으로 변경 -->
                            <div style="display: flex; gap: 12px; margin-bottom: 24px; background: linear-gradient(135deg, #f0f4ff 0%, #e8f0fe 100%); padding: 12px; border-radius: 16px; border: 2px solid #c7d2fe;">
                                <button type="button" id="tab-single" onclick="switchTab('single')" style="flex: 1; padding: 16px 24px; background: linear-gradient(135deg, #4f46e5 0%, #4f46e5 100%); color: white; border: none; border-radius: 12px; font-weight: 700; cursor: pointer; font-size: 16px; box-shadow: 0 4px 12px rgba(102,126,234,0.4); transition: all 0.2s;">📷 개별 문제</button>
                                <button type="button" id="tab-pdf" onclick="switchTab('pdf')" style="flex: 1; padding: 16px 24px; background: white; color: #4b5563; border: 2px solid #d1d5db; border-radius: 12px; font-weight: 700; cursor: pointer; font-size: 16px; transition: all 0.2s;">📄 PDF 일괄 업로드</button>
                            </div>

                            <!-- Single problem form -->
                            <div id="form-single">
                                <form id="add-problem-form" onsubmit="handleAddProblem(event)">
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
                                        <div>
                                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">연도</label>
                                            <input type="number" name="year" required min="2000" max="2030" value="2026" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px;">
                                        </div>
                                        <div>
                                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">시험 유형</label>
                                            <select name="exam" required style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px;">
                                                <option value="CSAT">수능 (CSAT)</option>
                                                <option value="KICE6">6월 평가원</option>
                                                <option value="KICE9">9월 평가원</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">문제 번호</label>
                                            <input type="number" name="question_no" required min="1" max="30" value="1" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px;">
                                        </div>
                                        <div>
                                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">난이도</label>
                                            <select name="score" required style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px;">
                                                <option value="2">2점</option>
                                                <option value="3" selected>3점</option>
                                                <option value="4">4점</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div style="margin-bottom: 15px;">
                                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">단원</label>
                                        <input type="text" name="unit" placeholder="예: 미분, 적분, 수열" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px;">
                                    </div>
                                    <div style="margin-bottom: 15px;">
                                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">정답</label>
                                        <input type="text" name="answer" placeholder="예: 5" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px;">
                                    </div>
                                    <div style="margin-bottom: 20px;">
                                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">문제 이미지 또는 PDF</label>
                                        <input type="file" id="single-file-input" name="image" accept="image/*,.pdf" required style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px;" onchange="handleSingleFileChange(event)">
                                        <p style="font-size: 12px; color: #666; margin-top: 5px;">이미지 또는 PDF 파일 (PDF는 페이지 선택 가능)</p>
                                    </div>
                                    <!-- PDF page selector and crop area -->
                                    <div id="single-pdf-pages" style="display: none; margin-bottom: 20px;">
                                        <div style="padding: 16px; background: linear-gradient(135deg, #4f46e5 0%, #4f46e5 100%); border-radius: 10px; margin-bottom: 12px;">
                                            <div style="display: flex; align-items: center; justify-content: center; gap: 12px;">
                                                <button type="button" onclick="singlePdfPrevPage()" id="single-prev-btn" style="padding: 8px 16px; background: white; color: #4f46e5; border: none; border-radius: 6px; font-weight: 600; cursor: pointer;">◀ 이전</button>
                                                <select id="single-page-select" onchange="singlePdfGoToPage(this.value)" style="padding: 8px 12px; border: none; border-radius: 6px; font-weight: 600;"></select>
                                                <span id="single-page-info" style="color: white; font-weight: 600;"></span>
                                                <button type="button" onclick="singlePdfNextPage()" id="single-next-btn" style="padding: 8px 16px; background: white; color: #4f46e5; border: none; border-radius: 6px; font-weight: 600; cursor: pointer;">다음 ▶</button>
                                            </div>
                                        </div>
                                        <div style="background: #f8fafc; border-radius: 10px; padding: 16px;">
                                            <div style="font-size: 14px; font-weight: 600; color: #475569; margin-bottom: 12px;">🖱️ 마우스로 드래그하여 문제 영역을 선택하세요</div>
                                            <div id="single-crop-wrapper" style="position: relative; display: inline-block; max-width: 100%; cursor: crosshair;">
                                                <canvas id="single-pdf-canvas" style="max-width: 100%; display: block;"></canvas>
                                                <div id="single-crop-selection" style="display: none; position: absolute; border: 2px dashed #4f46e5; background: rgba(102, 126, 234, 0.1); pointer-events: none;"></div>
                                            </div>
                                            <div style="margin-top: 12px; display: flex; gap: 10px; justify-content: center;">
                                                <button type="button" id="single-crop-btn" onclick="applySingleCrop()" style="display: none; padding: 10px 24px; background: #10B981; color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer;">✂️ 이 영역 크롭</button>
                                            </div>
                                        </div>
                                    </div>
                                    <!-- Cropped image preview -->
                                    <div id="single-cropped-area" style="display: none; margin-bottom: 20px; padding: 16px; background: #ecfdf5; border-radius: 10px; border: 1px solid #10b981;">
                                        <div style="font-size: 14px; font-weight: 600; color: #065f46; margin-bottom: 12px;">✅ 크롭 완료</div>
                                        <div style="text-align: center;">
                                            <img id="single-cropped-preview" src="" style="max-width: 100%; max-height: 200px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                                        </div>
                                        <div style="margin-top: 12px; text-align: center;">
                                            <button type="button" onclick="resetSingleCrop()" style="padding: 8px 16px; background: #e5e7eb; color: #374151; border: none; border-radius: 6px; font-weight: 600; cursor: pointer;">다시 크롭</button>
                                        </div>
                                    </div>
                                    <!-- Hidden input for cropped image data -->
                                    <input type="hidden" id="single-converted-image" name="converted_image">
                                    <div style="display: flex; gap: 10px; justify-content: flex-end;">
                                        <button type="submit" id="single-submit-btn" style="padding: 12px 24px; background: #10B981; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 15px;">✓ 추가</button>
                                        <button type="button" onclick="closeAddProblemModal()" style="padding: 12px 24px; background: #e0e0e0; color: #333; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 15px;">취소</button>
                                    </div>
                                </form>
                            </div>

                            <!-- PDF batch upload form -->
                            <div id="form-pdf" style="display: none;">
                                <form id="pdf-upload-form" onsubmit="handlePdfUpload(event)">
                                    <div style="background: #f0f9ff; padding: 16px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #0ea5e9;">
                                        <h4 style="margin: 0 0 8px 0; color: #0369a1;">📄 PDF 일괄 처리</h4>
                                        <p style="margin: 0; font-size: 14px; color: #0c4a6e;">수능/평가원 PDF 파일을 업로드하면 자동으로 문제별로 분리하여 저장합니다.</p>
                                        <ul style="margin: 10px 0 0 0; padding-left: 20px; font-size: 13px; color: #0c4a6e;">
                                            <li>2026 수능: 2열 레이아웃 자동 인식</li>
                                            <li>2022-2025: 기존 레이아웃 지원</li>
                                            <li>Q1~Q22 수학 공통 자동 분리</li>
                                        </ul>
                                    </div>
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
                                        <div>
                                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">연도</label>
                                            <input type="number" name="year" required min="2000" max="2030" value="2026" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px;">
                                        </div>
                                        <div>
                                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">시험 유형</label>
                                            <select name="exam" required style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px;">
                                                <option value="CSAT">수능 (CSAT)</option>
                                                <option value="KICE6">6월 평가원</option>
                                                <option value="KICE9">9월 평가원</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div style="margin-bottom: 20px;">
                                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">PDF 파일</label>
                                        <input type="file" name="pdf" accept=".pdf" required style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px;">
                                        <p style="font-size: 12px; color: #666; margin-top: 5px;">수능/평가원 수학 영역 PDF 파일</p>
                                    </div>
                                    <div id="pdf-progress" style="display: none; margin-bottom: 20px;">
                                        <div style="background: #e5e7eb; border-radius: 10px; overflow: hidden;">
                                            <div id="pdf-progress-bar" style="width: 0%; height: 24px; background: linear-gradient(90deg, #4f46e5, #4f46e5); transition: width 0.3s;"></div>
                                        </div>
                                        <p id="pdf-progress-text" style="text-align: center; margin-top: 8px; font-size: 14px; color: #4b5563;">처리 중...</p>
                                    </div>
                                    <div style="display: flex; gap: 10px; justify-content: flex-end;">
                                        <button type="submit" id="pdf-submit-btn" style="padding: 12px 24px; background: #4f46e5; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 15px;">📤 업로드 및 처리</button>
                                        <button type="button" onclick="closeAddProblemModal()" style="padding: 12px 24px; background: #e0e0e0; color: #333; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 15px;">취소</button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', modalHtml);
        }

        function switchTab(tab) {
            console.log('[Tab] Switching to:', tab);
            const tabSingle = document.getElementById('tab-single');
            const tabPdf = document.getElementById('tab-pdf');
            const formSingle = document.getElementById('form-single');
            const formPdf = document.getElementById('form-pdf');
            console.log('[Tab] Elements found:', {tabSingle: !!tabSingle, tabPdf: !!tabPdf, formSingle: !!formSingle, formPdf: !!formPdf});

            if (tab === 'single') {
                tabSingle.style.background = 'linear-gradient(135deg, #4f46e5 0%, #4f46e5 100%)';
                tabSingle.style.color = 'white';
                tabSingle.style.border = 'none';
                tabSingle.style.boxShadow = '0 4px 12px rgba(102,126,234,0.4)';
                tabPdf.style.background = 'white';
                tabPdf.style.color = '#4b5563';
                tabPdf.style.border = '2px solid #d1d5db';
                tabPdf.style.boxShadow = 'none';
                formSingle.style.display = 'block';
                formPdf.style.display = 'none';
            } else {
                tabPdf.style.background = 'linear-gradient(135deg, #4f46e5 0%, #4f46e5 100%)';
                tabPdf.style.color = 'white';
                tabPdf.style.border = 'none';
                tabPdf.style.boxShadow = '0 4px 12px rgba(102,126,234,0.4)';
                tabSingle.style.background = 'white';
                tabSingle.style.color = '#4b5563';
                tabSingle.style.border = '2px solid #d1d5db';
                tabSingle.style.boxShadow = 'none';
                formSingle.style.display = 'none';
                formPdf.style.display = 'block';
            }
        }

        // Single problem PDF handling
        let singlePdfDoc = null;
        let singleCurrentPage = 1;
        let singleTotalPages = 0;
        let singleCropRect = null;
        let singleIsCropping = false;
        let singleCropStart = null;

        async function handleSingleFileChange(event) {
            const file = event.target.files[0];
            if (!file) return;

            const pdfPagesDiv = document.getElementById('single-pdf-pages');
            const croppedArea = document.getElementById('single-cropped-area');

            // Reset crop state
            croppedArea.style.display = 'none';
            singleCropRect = null;
            document.getElementById('single-crop-btn').style.display = 'none';
            document.getElementById('single-crop-selection').style.display = 'none';

            if (file.type === 'application/pdf') {
                // Show PDF page selector
                pdfPagesDiv.style.display = 'block';

                try {
                    if (!window.pdfjsLib) {
                        alert('PDF 라이브러리를 불러오는 중입니다. 잠시 후 다시 시도해주세요.');
                        return;
                    }

                    const arrayBuffer = await file.arrayBuffer();
                    const loadingTask = window.pdfjsLib.getDocument({ data: arrayBuffer });
                    singlePdfDoc = await loadingTask.promise;
                    singleTotalPages = singlePdfDoc.numPages;
                    singleCurrentPage = 1;

                    // Populate page selector
                    const pageSelect = document.getElementById('single-page-select');
                    pageSelect.innerHTML = '';
                    for (let i = 1; i <= singleTotalPages; i++) {
                        const option = document.createElement('option');
                        option.value = i;
                        option.textContent = i + '페이지';
                        pageSelect.appendChild(option);
                    }

                    document.getElementById('single-page-info').textContent = '/ ' + singleTotalPages + '페이지';

                    // Render first page
                    await renderSinglePdfPage(1);

                    // Setup crop handlers
                    setupSingleCropHandlers();
                } catch (error) {
                    console.error('PDF load error:', error);
                    alert('PDF 로드 실패: ' + error.message);
                    pdfPagesDiv.style.display = 'none';
                }
            } else {
                // For images, also show crop interface
                pdfPagesDiv.style.display = 'block';
                singlePdfDoc = null;

                // Hide page navigation for images
                document.querySelector('#single-pdf-pages > div:first-child').style.display = 'none';

                const reader = new FileReader();
                reader.onload = function(e) {
                    const img = new Image();
                    img.onload = function() {
                        const canvas = document.getElementById('single-pdf-canvas');
                        const context = canvas.getContext('2d');

                        // Scale down if too large
                        let scale = 1;
                        if (img.width > 800) scale = 800 / img.width;

                        canvas.width = img.width * scale;
                        canvas.height = img.height * scale;
                        context.drawImage(img, 0, 0, canvas.width, canvas.height);

                        setupSingleCropHandlers();
                    };
                    img.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        }

        function setupSingleCropHandlers() {
            const canvas = document.getElementById('single-pdf-canvas');
            const selection = document.getElementById('single-crop-selection');
            const wrapper = document.getElementById('single-crop-wrapper');

            // Remove old handlers
            canvas.onmousedown = null;
            canvas.onmousemove = null;
            canvas.onmouseup = null;

            canvas.onmousedown = function(e) {
                const rect = canvas.getBoundingClientRect();
                singleCropStart = {
                    x: e.clientX - rect.left,
                    y: e.clientY - rect.top
                };
                singleIsCropping = true;
                selection.style.display = 'block';
                selection.style.left = singleCropStart.x + 'px';
                selection.style.top = singleCropStart.y + 'px';
                selection.style.width = '0px';
                selection.style.height = '0px';
            };

            canvas.onmousemove = function(e) {
                if (!singleIsCropping) return;
                const rect = canvas.getBoundingClientRect();
                const currentX = e.clientX - rect.left;
                const currentY = e.clientY - rect.top;

                const left = Math.min(singleCropStart.x, currentX);
                const top = Math.min(singleCropStart.y, currentY);
                const width = Math.abs(currentX - singleCropStart.x);
                const height = Math.abs(currentY - singleCropStart.y);

                selection.style.left = left + 'px';
                selection.style.top = top + 'px';
                selection.style.width = width + 'px';
                selection.style.height = height + 'px';

                singleCropRect = { left, top, width, height };
            };

            canvas.onmouseup = function(e) {
                if (singleIsCropping && singleCropRect && singleCropRect.width > 10 && singleCropRect.height > 10) {
                    document.getElementById('single-crop-btn').style.display = 'inline-block';
                }
                singleIsCropping = false;
            };
        }

        function applySingleCrop() {
            if (!singleCropRect) return;

            const canvas = document.getElementById('single-pdf-canvas');
            const context = canvas.getContext('2d');

            // Get the actual scale between display and canvas
            const displayWidth = canvas.clientWidth;
            const actualWidth = canvas.width;
            const scale = actualWidth / displayWidth;

            // Scale crop coordinates
            const cropX = singleCropRect.left * scale;
            const cropY = singleCropRect.top * scale;
            const cropW = singleCropRect.width * scale;
            const cropH = singleCropRect.height * scale;

            // Create cropped canvas
            const croppedCanvas = document.createElement('canvas');
            croppedCanvas.width = cropW;
            croppedCanvas.height = cropH;
            const croppedCtx = croppedCanvas.getContext('2d');
            croppedCtx.drawImage(canvas, cropX, cropY, cropW, cropH, 0, 0, cropW, cropH);

            // Store cropped image
            const dataUrl = croppedCanvas.toDataURL('image/png');
            document.getElementById('single-converted-image').value = dataUrl;

            // Show preview
            document.getElementById('single-cropped-preview').src = dataUrl;
            document.getElementById('single-cropped-area').style.display = 'block';
            document.getElementById('single-pdf-pages').style.display = 'none';
        }

        function resetSingleCrop() {
            document.getElementById('single-cropped-area').style.display = 'none';
            document.getElementById('single-pdf-pages').style.display = 'block';
            document.getElementById('single-converted-image').value = '';
            document.getElementById('single-crop-selection').style.display = 'none';
            document.getElementById('single-crop-btn').style.display = 'none';
            singleCropRect = null;

            // Re-show page nav if PDF
            if (singlePdfDoc) {
                document.querySelector('#single-pdf-pages > div:first-child').style.display = 'block';
            }
        }

        async function renderSinglePdfPage(pageNum) {
            if (!singlePdfDoc) return;

            try {
                const page = await singlePdfDoc.getPage(pageNum);
                const viewport = page.getViewport({ scale: 2.0 });

                const canvas = document.getElementById('single-pdf-canvas');
                const context = canvas.getContext('2d');
                canvas.width = viewport.width;
                canvas.height = viewport.height;

                await page.render({
                    canvasContext: context,
                    viewport: viewport
                }).promise;

                // Reset crop selection
                document.getElementById('single-crop-selection').style.display = 'none';
                document.getElementById('single-crop-btn').style.display = 'none';
                singleCropRect = null;

                // Update UI
                document.getElementById('single-page-select').value = pageNum;
                document.getElementById('single-prev-btn').disabled = pageNum <= 1;
                document.getElementById('single-next-btn').disabled = pageNum >= singleTotalPages;

                // Show page nav
                document.querySelector('#single-pdf-pages > div:first-child').style.display = 'flex';
            } catch (error) {
                console.error('Page render error:', error);
            }
        }

        function singlePdfPrevPage() {
            if (singleCurrentPage > 1) {
                singleCurrentPage--;
                renderSinglePdfPage(singleCurrentPage);
            }
        }

        function singlePdfNextPage() {
            if (singleCurrentPage < singleTotalPages) {
                singleCurrentPage++;
                renderSinglePdfPage(singleCurrentPage);
            }
        }

        function singlePdfGoToPage(pageNum) {
            singleCurrentPage = parseInt(pageNum);
            renderSinglePdfPage(singleCurrentPage);
        }

        async function handlePdfUpload(event) {
            event.preventDefault();
            console.log('[PDF Upload] Form submitted');
            const form = event.target;
            const formData = new FormData(form);

            // Debug: Check form data
            console.log('[PDF Upload] Year:', formData.get('year'));
            console.log('[PDF Upload] Exam:', formData.get('exam'));
            console.log('[PDF Upload] PDF file:', formData.get('pdf'));

            const submitBtn = document.getElementById('pdf-submit-btn');
            const progressDiv = document.getElementById('pdf-progress');
            const progressBar = document.getElementById('pdf-progress-bar');
            const progressText = document.getElementById('pdf-progress-text');

            submitBtn.disabled = true;
            submitBtn.textContent = '처리 중...';
            progressDiv.style.display = 'block';
            progressBar.style.width = '10%';
            progressText.textContent = 'PDF 업로드 중...';

            try {
                const response = await fetch('/problem/upload-pdf', {
                    method: 'POST',
                    credentials: 'include',
                    body: formData
                });

                progressBar.style.width = '50%';
                progressText.textContent = '문제 분리 중...';

                const data = await response.json();

                if (response.ok) {
                    progressBar.style.width = '100%';
                    progressText.textContent = '완료!';

                    setTimeout(() => {
                        alert('PDF 처리 완료!\\n\\n' +
                            '총 문제: ' + data.total_problems + '개\\n' +
                            '업로드 성공: ' + data.uploaded + '개' +
                            (data.skipped_pages > 0 ? '\\n\\n(선택과목 ' + data.skipped_pages + '페이지는 스킵됨)' : ''));
                        closeAddProblemModal();
                        loadProblems();
                        loadStats();
                    }, 500);
                } else {
                    throw new Error(data.detail || 'PDF 처리 실패');
                }
            } catch (error) {
                console.error('Error:', error);
                progressBar.style.background = '#ef4444';
                progressText.textContent = '오류: ' + error.message;
                alert('PDF 처리 중 오류가 발생했습니다: ' + error.message);
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = '📤 업로드 및 처리';
            }
        }

        function closeAddProblemModal() {
            const modal = document.getElementById('add-problem-modal');
            if (modal) modal.remove();
        }

        async function handleAddProblem(event) {
            event.preventDefault();
            const form = event.target;
            const formData = new FormData(form);

            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = '업로드 중...';

            try {
                // Check if we have a cropped image (from PDF or image)
                const convertedImage = document.getElementById('single-converted-image').value;
                if (convertedImage) {
                    // Convert data URL to Blob and replace the file
                    const response = await fetch(convertedImage);
                    const blob = await response.blob();
                    formData.delete('image');
                    formData.append('image', blob, 'cropped_problem.png');
                }

                const uploadResponse = await fetch('/problem/add', {
                    method: 'POST',
                    credentials: 'include',
                    body: formData
                });

                const data = await uploadResponse.json();

                if (uploadResponse.ok) {
                    alert('문제가 추가되었습니다: ' + data.problem_id);
                    closeAddProblemModal();
                    loadProblems();
                    loadStats();
                } else {
                    alert('오류: ' + (data.detail || 'Failed'));
                }
            } catch (error) {
                console.error('Error:', error);
                alert('문제 추가 중 오류가 발생했습니다: ' + error.message);
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = '✓ 추가';
            }
        }

        loadStats(); loadProblems();
    </script>

    <!-- Crop Modal Root -->
    <div id="crop-modal-root"></div>

    <!-- PDF.js for PDF rendering -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <script>
      // Set PDF.js worker
      if (window.pdfjsLib) {
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
      }
    </script>

    <!-- React and Babel -->
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>

    <!-- Shared Crop Components -->
    <script type="text/babel" src="/static/shared-crop-components.jsx?v=20"></script>

    <!-- Crop Modal Component -->
    <script type="text/babel" src="/static/crop-modal.jsx?v=20"></script>
</body>
</html>
"""
    return HTMLResponse(
        content=html,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )


# NOTE: This route must come AFTER /admin, /list, /ready, /stats
@router.get("/{problem_id}/metadata")
async def get_problem_metadata(request: Request, problem_id: str):
    """
    Get problem metadata for crop modal
    """
    user = get_user_from_session(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        supabase = SupabaseService()
        problem = supabase.get_problem(problem_id)
        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found")

        return {
            "problem_id": problem_id,
            "year": problem.get("year"),
            "exam": problem.get("exam"),
            "question_no": problem.get("question_no"),
            "image_url": problem.get("problem_image_url") or problem.get("image_url") or f"https://gusahlxqyyqmaalwdtjw.supabase.co/storage/v1/object/public/problem-images-v2/{problem_id}.png",
            "difficulty": f"{problem.get('score', 3)}점",
            "category": problem.get("unit", "미분"),
            "subject": problem.get("subject", "수1"),
            "answer": problem.get("answer_verified") or problem.get("answer", ""),
            "solution": problem.get("solution", "")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{problem_id}")
async def get_problem(request: Request, problem_id: str):
    """
    Get single problem by ID
    """
    user = get_user_from_session(request)

    try:
        supabase = SupabaseService()
        problem = supabase.get_problem(problem_id)
        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found")
        return problem
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===========================================
# Send Problem APIs
# ===========================================

@router.post("/send")
async def send_problem(request: Request, body: SendProblemRequest):
    """
    Send a single problem to logged-in user
    """
    user = get_user_from_session(request)

    access_token = user.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token")

    try:
        supabase = SupabaseService()
        problem = supabase.get_problem(body.problem_id)

        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found")

        # Generate optimized card image for KakaoTalk (800x800 square)
        score = problem.get("score")
        difficulty = f"{score}점" if score else None

        # Get problem image URL (try both field names for backward compatibility)
        problem_image = problem.get("problem_image_url") or problem.get("image_url")
        print(f"[Send Card] Starting generation for {body.problem_id}, image_url={problem_image}")
        card_image_url = None

        if not problem_image:
            raise HTTPException(status_code=400, detail=f"No image URL for problem {body.problem_id}")

        try:
            card_generator = CardImageGenerator()

            # Generate card image bytes
            card_bytes = card_generator.generate_card(
                problem_image_url=problem_image,
                title=f"{problem.get('year')} {problem.get('exam')} {problem.get('question_no')}번",
                year=problem.get("year"),
                exam=problem.get("exam"),
                number=problem.get("question_no"),
                difficulty=difficulty,
                unit=problem.get("unit")
            )

            print(f"[Send Card] Generated {len(card_bytes)} bytes")

            # Upload card to Supabase Storage
            import requests
            supabase_url = os.getenv("SUPABASE_URL")
            service_key = os.getenv("SUPABASE_SERVICE_KEY")
            bucket = "problem-images-v2"
            card_filename = f"{body.problem_id}_card.png"
            upload_url = f"{supabase_url}/storage/v1/object/{bucket}/{card_filename}"

            headers = {
                "Authorization": f"Bearer {service_key}",
                "Content-Type": "image/png",
                "x-upsert": "true"
            }

            upload_resp = requests.post(upload_url, headers=headers, data=card_bytes)

            print(f"[Send Card] Upload response: {upload_resp.status_code}")

            if upload_resp.status_code in [200, 201]:
                # Use card image for KakaoTalk message
                card_image_url = f"{supabase_url}/storage/v1/object/public/{bucket}/{card_filename}"
                print(f"[Send Card] Success! URL: {card_image_url}")
            else:
                print(f"[Send Card] Upload failed: {upload_resp.text}")
                card_image_url = problem_image

        except Exception as e:
            import traceback
            print(f"[Send Card] ERROR: {str(e)}")
            print(traceback.format_exc())
            card_image_url = problem_image

        # Fallback to original if card generation failed
        if not card_image_url:
            card_image_url = problem_image
            print(f"[Send Card] Using original image")

        # Build problem viewer URL
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        viewer_url = f"{base_url}/problem/view/{body.problem_id}"
        print(f"[Problem Send] Viewer URL: {viewer_url}")

        print(f"[Problem Send] Calling send_math_problem with:")
        print(f"  - access_token: {access_token[:20]}... (len={len(access_token)})")
        print(f"  - problem_image_url: {card_image_url}")
        print(f"  - button_url: {viewer_url}")
        import sys
        sys.stdout.flush()

        try:
            result = message_service.send_math_problem(
                access_token=access_token,
                problem_id=body.problem_id,
                problem_text=problem.get("extract_text", "")[:500],
                problem_image_url=card_image_url,  # Use optimized card image
                year=problem.get("year"),
                exam=problem.get("exam"),
                number=problem.get("question_no"),
                difficulty=difficulty,
                unit=problem.get("unit"),
                button_title="🎯 문제 풀기",
                button_url=viewer_url
            )
            print(f"[Problem Send] send_math_problem returned success={result.get('success')}")
        except Exception as msg_error:
            import traceback
            import sys
            error_msg = f"[Problem Send] send_math_problem EXCEPTION: {str(msg_error)}"
            traceback_str = traceback.format_exc()
            print(error_msg, file=sys.stderr)
            print(traceback_str, file=sys.stderr)
            sys.stderr.flush()
            raise HTTPException(status_code=500, detail=f"Message send failed: {str(msg_error)}")

        if result.get("success"):
            # Update problem status
            supabase.update_problem(body.problem_id, {"status": "sent"})

            # Record user history (optional - if table exists)
            try:
                supabase.client.table("user_problems").insert({
                    "user_id": user.get("id"),
                    "problem_id": body.problem_id
                }).execute()
            except:
                pass  # Ignore if table doesn't exist

            return {"message": "Problem sent successfully", "problem_id": body.problem_id}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to send: {result.get('error')}"
            )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        import sys
        error_traceback = traceback.format_exc()
        error_msg = f"[Send Problem Error] {str(e)}\n{error_traceback}"
        print(error_msg, file=sys.stderr)
        sys.stderr.flush()
        raise HTTPException(status_code=500, detail=f"Send failed: {str(e)}")


@router.post("/send-bulk")
async def send_bulk_problems(request: Request, body: BulkSendRequest):
    """
    Send multiple problems to logged-in user
    """
    user = get_user_from_session(request)

    access_token = user.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token")

    if not body.problem_ids or len(body.problem_ids) == 0:
        raise HTTPException(status_code=400, detail="No problems specified")

    if len(body.problem_ids) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 problems per bulk send")

    success_count = 0
    failure_count = 0
    errors = []

    for problem_id in body.problem_ids:
        try:
            # Reuse the single send logic
            req = SendProblemRequest(problem_id=problem_id)
            await send_problem(request, req)
            success_count += 1
            print(f"[Bulk Send] Success: {problem_id}")
        except Exception as e:
            failure_count += 1
            error_msg = str(e)
            errors.append(f"{problem_id}: {error_msg}")
            print(f"[Bulk Send] Failed: {problem_id} - {error_msg}")

    return {
        "success_count": success_count,
        "failure_count": failure_count,
        "total": len(body.problem_ids),
        "errors": errors if errors else None
    }


@router.post("/upload-pdf")
async def upload_pdf_batch(
    request: Request,
    year: int = Form(...),
    exam: str = Form(...),
    pdf: UploadFile = File(...)
):
    """
    Upload and process entire PDF exam file
    Automatically splits into individual problems using templates
    """
    user = get_user_from_session(request)

    try:
        import tempfile
        from pathlib import Path as PyPath

        print(f"[PDF Upload] Starting: {year} {exam}, file: {pdf.filename}")

        # Save uploaded PDF to temp file
        pdf_bytes = await pdf.read()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_bytes)
            tmp_pdf_path = tmp.name

        print(f"[PDF Upload] Saved to temp: {tmp_pdf_path}, size: {len(pdf_bytes)} bytes")

        # Import pipeline components
        import sys
        sys.path.insert(0, str(PyPath(__file__).parent.parent / "src"))

        from pdf_converter import PDFConverter
        from page_splitter import process_exam_pdf
        from PIL import Image

        # Step 1: Convert PDF to images
        print(f"[PDF Upload] Converting PDF to images...")
        converter = PDFConverter(dpi=250)

        output_dir = PyPath(tempfile.mkdtemp())
        page_images_paths = converter.pdf_to_images(PyPath(tmp_pdf_path), output_folder=output_dir)

        print(f"[PDF Upload] Created {len(page_images_paths)} page images")

        # Load images
        pdf_pages = [Image.open(p) for p in page_images_paths]

        # Step 2: Split into individual problems
        print(f"[PDF Upload] Splitting into problems...")
        questions_dir = output_dir / f"{year}_{exam}_questions"
        questions_dir.mkdir(exist_ok=True)

        summary = process_exam_pdf(
            pdf_pages=pdf_pages,
            exam=exam,
            year=year,
            output_dir=str(questions_dir),
            verify_ocr=False  # Skip OCR for speed
        )

        print(f"[PDF Upload] Split complete: {summary['total_problems']} problems")

        # Step 3: Upload to Supabase Storage
        supabase_url = os.getenv("SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_KEY")
        bucket = "problem-images-v2"

        import requests as http_requests

        uploaded_count = 0
        supabase = SupabaseService()

        for result in summary.get("results", []):
            problem_id = result["problem_id"]
            filepath = result["filepath"]
            question_no = result["question_no"]

            # Skip pages without templates (Q00 = 선택과목 등)
            if question_no == 0:
                print(f"[PDF Upload] Skipping {problem_id} (no template)")
                continue

            try:
                # Read image file
                with open(filepath, "rb") as f:
                    image_bytes = f.read()

                # Upload to storage
                filename = f"{problem_id}.png"
                upload_url = f"{supabase_url}/storage/v1/object/{bucket}/{filename}"

                headers = {
                    "Authorization": f"Bearer {service_key}",
                    "Content-Type": "image/png",
                    "x-upsert": "true"
                }

                upload_resp = http_requests.post(upload_url, headers=headers, data=image_bytes)

                if upload_resp.status_code in [200, 201]:
                    image_url = f"{supabase_url}/storage/v1/object/public/{bucket}/{filename}"

                    # Save to database
                    problem_data = {
                        "problem_id": problem_id,
                        "year": year,
                        "exam": exam,
                        "question_no": question_no,
                        "score": 3,  # Default score
                        "image_url": image_url,
                        "problem_image_url": image_url,
                        "status": "needs_review" if result.get("needs_review") else "ready"
                    }

                    supabase.client.table("problems").upsert(problem_data).execute()
                    uploaded_count += 1
                    print(f"[PDF Upload] Uploaded: {problem_id}")
                else:
                    print(f"[PDF Upload] Upload failed for {problem_id}: {upload_resp.text}")

            except Exception as e:
                print(f"[PDF Upload] Error processing {problem_id}: {e}")

        # Cleanup temp files
        try:
            os.remove(tmp_pdf_path)
            import shutil
            shutil.rmtree(output_dir)
        except:
            pass

        # Count valid problems (non-Q00)
        valid_problems = len([r for r in summary.get("results", []) if r["question_no"] > 0])
        print(f"[PDF Upload] Complete! Uploaded {uploaded_count}/{valid_problems} problems (skipped {summary['needs_review_count']} pages without templates)")

        return {
            "message": "PDF processed successfully",
            "total_problems": valid_problems,
            "uploaded": uploaded_count,
            "needs_review": 0,  # needs_review now means something else
            "skipped_pages": summary["needs_review_count"]
        }

    except Exception as e:
        import traceback
        print(f"[PDF Upload Error] {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")


@router.post("/add")
async def add_problem(
    request: Request,
    year: int = Form(...),
    exam: str = Form(...),
    question_no: int = Form(...),
    score: int = Form(...),
    unit: str = Form(None),
    answer: str = Form(None),
    image: UploadFile = File(...)
):
    """
    Add a new problem manually via admin interface
    """
    user = get_user_from_session(request)

    try:
        # Generate problem_id
        problem_id = f"{year}_{exam}_Q{question_no:02d}"
        print(f"[Add Problem] Creating problem: {problem_id}")

        # Read image file
        image_bytes = await image.read()
        print(f"[Add Problem] Image size: {len(image_bytes)} bytes, type: {image.content_type}")

        # Upload to Supabase Storage
        supabase_url = os.getenv("SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_KEY")
        bucket = "problem-images-v2"
        filename = f"{problem_id}.png"
        upload_url = f"{supabase_url}/storage/v1/object/{bucket}/{filename}"

        headers = {
            "Authorization": f"Bearer {service_key}",
            "Content-Type": image.content_type or "image/png",
            "x-upsert": "true"
        }

        import requests
        upload_resp = requests.post(upload_url, headers=headers, data=image_bytes)

        if upload_resp.status_code not in [200, 201]:
            print(f"[Add Problem] Upload failed: {upload_resp.text}")
            raise HTTPException(status_code=500, detail="Image upload failed")

        image_url = f"{supabase_url}/storage/v1/object/public/{bucket}/{filename}"
        print(f"[Add Problem] Image uploaded: {image_url}")

        # Insert into database
        supabase = SupabaseService()
        problem_data = {
            "problem_id": problem_id,
            "year": year,
            "exam": exam,
            "question_no": question_no,
            "score": score,
            "unit": unit,
            "answer": answer,
            "image_url": image_url,
            "status": "ready",
            "problem_image_url": image_url  # For compatibility
        }

        result = supabase.client.table("problems").upsert(problem_data).execute()
        print(f"[Add Problem] Database insert successful")

        return {
            "message": "Problem added successfully",
            "problem_id": problem_id,
            "image_url": image_url
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[Add Problem Error] {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to add problem: {str(e)}")


@router.post("/send-hint/{problem_id}/{level}")
async def send_hint(request: Request, problem_id: str, level: int):
    """
    Send hint for a problem (level 1, 2, or 3)
    """
    user = get_user_from_session(request)

    if level not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="Hint level must be 1, 2, or 3")

    access_token = user.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token")

    try:
        supabase = SupabaseService()
        problem = supabase.get_problem(problem_id)

        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found")

        # Get hint text
        hint_field = f"hint_{level}"
        hint_text = problem.get(hint_field)

        if not hint_text:
            raise HTTPException(status_code=404, detail=f"Hint {level} not available")

        result = message_service.send_hint(
            access_token=access_token,
            hint_level=level,
            hint_text=hint_text
        )

        if result.get("success"):
            return {"message": f"Hint {level} sent successfully"}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to send hint: {result.get('error')}"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-answer/{problem_id}")
async def send_answer(request: Request, problem_id: str, user_answer: Optional[str] = None):
    """
    Send answer and solution for a problem
    """
    user = get_user_from_session(request)

    access_token = user.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token")

    try:
        supabase = SupabaseService()
        problem = supabase.get_problem(problem_id)

        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found")

        answer = problem.get("answer_verified") or problem.get("answer") or "N/A"
        solution = problem.get("solution") or "풀이가 아직 준비되지 않았습니다."

        # Check if user answer is correct
        is_correct = None
        if user_answer:
            is_correct = str(user_answer).strip() == str(answer).strip()

        result = message_service.send_answer(
            access_token=access_token,
            answer=answer,
            solution=solution,
            is_correct=is_correct
        )

        if result.get("success"):
            return {
                "message": "Answer sent successfully",
                "answer": answer,
                "is_correct": is_correct
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to send answer: {result.get('error')}"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test", response_class=HTMLResponse)
async def test_view():
    """Simple test page to verify KakaoTalk webview works - NO AUTHENTICATION REQUIRED"""
    print("[Test Endpoint] Accessed - no authentication required")
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Test</title>
        <style>
            body { margin: 20px; font-family: sans-serif; background: #f0f0f0; }
            h1 { color: #333; }
            .box { background: white; padding: 20px; border-radius: 8px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <h1>Test Page</h1>
        <div class="box">
            <p>If you see this, the webview is working!</p>
            <p id="jstest">JavaScript is NOT working</p>
        </div>
        <script>
            document.getElementById('jstest').textContent = 'JavaScript IS working!';
            document.getElementById('jstest').style.color = 'green';
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.get("/view/{problem_id}", response_class=HTMLResponse)
async def view_problem(request: Request, problem_id: str):
    """
    Problem viewer page - opens in webview from KakaoTalk
    """
    print(f"[Problem Viewer] Accessed for problem_id: {problem_id}")
    print(f"[Problem Viewer] User-Agent: {request.headers.get('user-agent', 'N/A')}")

    supabase = SupabaseService()
    problem = supabase.get_problem(problem_id)

    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    # Build problem metadata
    problem_data = {
        "problem_id": problem_id,
        "year": problem.get("year"),
        "exam": problem.get("exam"),
        "number": problem.get("question_no"),
        "score": problem.get("score", 3),
        "difficulty": f"{problem.get('score', 3)}점",
        "unit": problem.get("unit"),
        "image_url": problem.get("problem_image_url") or problem.get("image_url") or f"https://gusahlxqyyqmaalwdtjw.supabase.co/storage/v1/object/public/problem-images-v2/{problem_id}.png",
        "answer": problem.get("answer_verified") or problem.get("answer"),
        "solution": problem.get("solution"),
    }

    print(f"[Problem Viewer] Loaded problem: {problem_data['year']} {problem_data['exam']} Q{problem_data['number']}")
    print(f"[Problem Viewer] Image URL: {problem_data['image_url']}")

    # Simple HTML viewer (KakaoTalk webview compatible)
    exam_name = {'CSAT': '수능', 'KICE6': '6월 평가원', 'KICE9': '9월 평가원'}.get(problem_data['exam'], problem_data['exam'])

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
    <title>{problem_data['year']} {exam_name} #{problem_data['number']}</title>
    <!-- KaTeX for math rendering -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Malgun Gothic', sans-serif;
            background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
            padding-bottom: 30px;
            min-height: 100vh;
        }}
        .header {{
            background: linear-gradient(135deg, #4f46e5 0%, #4f46e5 100%);
            color: white;
            padding: 24px 20px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
        }}
        .header h1 {{
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }}
        .header p {{
            font-size: 14px;
            opacity: 0.95;
            font-weight: 500;
        }}
        .image-container {{
            background: white;
            padding: 0;
            margin: 16px 0;
            text-align: center;
            width: 100%;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        }}
        .image-container img {{
            width: 100%;
            max-width: 100%;
            height: auto;
            display: block;
            /* High-quality image rendering */
            image-rendering: -webkit-optimize-contrast;
            image-rendering: crisp-edges;
            -ms-interpolation-mode: nearest-neighbor;
        }}
        .answer-section {{
            background: white;
            padding: 24px;
            margin: 16px 16px 12px 16px;
            border-radius: 16px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        }}
        .answer-section label {{
            display: block;
            font-weight: 600;
            margin-bottom: 12px;
            color: #2d3748;
            font-size: 15px;
        }}
        .answer-section input {{
            width: 100%;
            padding: 16px;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            font-size: 16px;
            transition: all 0.3s ease;
            background: #f8fafc;
        }}
        .answer-section input:focus {{
            border-color: #4f46e5;
            outline: none;
            background: white;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            transform: translateY(-2px);
        }}
        .answer-section input.typing {{
            border-color: #a78bfa;
            box-shadow: 0 0 0 3px rgba(167, 139, 250, 0.1);
        }}
        .btn-container {{ padding: 0 16px; }}
        .btn {{
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, #4f46e5 0%, #4f46e5 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 17px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
            letter-spacing: -0.3px;
            position: relative;
            overflow: hidden;
        }}
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
        }}
        .btn:active {{
            transform: translateY(0);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }}
        .btn:disabled {{
            opacity: 0.8;
            cursor: not-allowed;
        }}
        .result {{
            padding: 24px;
            margin: 16px;
            border-radius: 16px;
            font-size: 16px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
            animation: slideIn 0.4s ease;
        }}
        .result.correct {{
            background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
            color: white;
        }}
        .result.wrong {{
            background: linear-gradient(135deg, #ef4444 0%, #f87171 100%);
            color: white;
        }}
        .result h2 {{
            margin-bottom: 12px;
            font-size: 20px;
            font-weight: 700;
        }}
        .debug {{
            background: rgba(255, 255, 255, 0.9);
            padding: 12px;
            margin: 12px;
            border-left: 4px solid #4f46e5;
            font-size: 11px;
            font-family: 'Courier New', monospace;
            border-radius: 8px;
            color: #64748b;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        @keyframes slideIn {{
            from {{
                opacity: 0;
                transform: translateY(-20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        @keyframes shake {{
            0%, 100% {{ transform: translateX(0); }}
            10%, 30%, 50%, 70%, 90% {{ transform: translateX(-5px); }}
            20%, 40%, 60%, 80% {{ transform: translateX(5px); }}
        }}
        @keyframes pulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.03); }}
            100% {{ transform: scale(1); }}
        }}
        @keyframes checkmark {{
            0% {{ transform: scale(0) rotate(45deg); opacity: 0; }}
            50% {{ transform: scale(1.2) rotate(45deg); opacity: 1; }}
            100% {{ transform: scale(1) rotate(45deg); opacity: 1; }}
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        .spinner {{
            display: inline-block;
            width: 18px;
            height: 18px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin-right: 8px;
            vertical-align: middle;
        }}
        .confetti {{
            position: fixed;
            width: 10px;
            height: 10px;
            background: #ffd700;
            position: absolute;
            animation: confettiFall 2s ease-out forwards;
        }}
        @keyframes confettiFall {{
            to {{
                transform: translateY(100vh) rotate(360deg);
                opacity: 0;
            }}
        }}
        .checkmark-circle {{
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: white;
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            animation: pulse 0.6s ease;
        }}
        .checkmark {{
            width: 30px;
            height: 50px;
            border-right: 5px solid #10b981;
            border-bottom: 5px solid #10b981;
            transform: rotate(45deg);
            animation: checkmark 0.5s ease 0.2s forwards;
            opacity: 0;
        }}
        .hint-section {{
            background: white;
            padding: 24px;
            margin: 12px 16px;
            border-radius: 16px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        }}
        .hint-btn {{
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }}
        .hint-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(245, 158, 11, 0.5);
        }}
        .hint-btn:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }}
        .hint-card {{
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            padding: 20px;
            margin-top: 16px;
            border-radius: 12px;
            border-left: 5px solid #f59e0b;
            box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
            animation: slideIn 0.4s ease;
        }}
        .hint-card h3 {{
            margin: 0 0 12px 0;
            color: #92400e;
            font-size: 18px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .hint-card p {{
            margin: 0;
            color: #78350f;
            font-size: 15px;
            line-height: 1.6;
        }}
        .hint-badge {{
            background: #f59e0b;
            color: white;
            padding: 4px 10px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 700;
        }}
        /* Math content styling */
        .math-content {{
            line-height: 1.8;
            font-size: 15px;
        }}
        .math-content .katex {{
            font-size: 1.05em;
        }}
        .math-content .katex-display {{
            margin: 12px 0;
            overflow-x: auto;
            overflow-y: hidden;
        }}
        .solution-section {{
            margin-top: 16px;
            padding: 16px;
            background: rgba(255,255,255,0.15);
            border-radius: 12px;
            border-top: 1px solid rgba(255,255,255,0.3);
        }}
        .solution-section h3 {{
            font-size: 15px;
            margin-bottom: 8px;
            font-weight: 700;
        }}
        .solution-step {{
            margin: 6px 0;
            padding-left: 8px;
            border-left: 2px solid rgba(255,255,255,0.3);
        }}
    </style>
</head>
<body>
    <div class="debug">
        DEBUG: Page loaded successfully<br>
        Problem ID: {problem_data['problem_id']}<br>
        Time: <span id="loadTime"></span>
    </div>

    <div class="header">
        <h1>{problem_data['year']} {exam_name}</h1>
        <p>{problem_data['number']}번 문제 | {problem_data['difficulty']} | {problem_data['unit']}</p>
    </div>

    <div class="image-container">
        <img src="{problem_data['image_url']}" alt="문제 이미지" loading="eager" fetchpriority="high" onerror="this.parentElement.innerHTML='<p style=color:red;>이미지를 불러올 수 없습니다</p>'">
    </div>

    <div class="answer-section">
        <label for="answerInput">답 입력:</label>
        <input type="text" id="answerInput" placeholder="답을 입력하세요" autofocus>
    </div>

    <div class="btn-container">
        <button class="btn" onclick="submitAnswer()">정답 확인</button>
    </div>

    <div class="hint-section">
        <button class="hint-btn" id="hintBtn" onclick="requestHint()">
            <span>💡</span>
            <span id="hintBtnText">힌트 1단계 보기</span>
        </button>
        <div id="hintContainer"></div>
    </div>

    <div id="result" style="display:none;"></div>

    <script>
        // Debug logging
        console.log('[Viewer] Page loaded');
        console.log('[Viewer] Problem ID: {problem_data['problem_id']}');
        console.log('[Viewer] Image URL: {problem_data['image_url']}');

        document.getElementById('loadTime').textContent = new Date().toLocaleTimeString();

        const answerInput = document.getElementById('answerInput');

        answerInput.addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') submitAnswer();
        }});

        // Add typing feedback
        let typingTimer;
        answerInput.addEventListener('input', function() {{
            this.classList.add('typing');
            clearTimeout(typingTimer);
            typingTimer = setTimeout(() => {{
                this.classList.remove('typing');
            }}, 500);
        }});

        async function submitAnswer() {{
            console.log('[Viewer] Submit button clicked');
            const userAnswer = document.getElementById('answerInput').value.trim();
            const resultDiv = document.getElementById('result');
            const submitBtn = document.querySelector('.btn');
            const answerInput = document.getElementById('answerInput');

            if (!userAnswer) {{
                // Shake input field to indicate error
                answerInput.style.animation = 'shake 0.5s';
                setTimeout(() => answerInput.style.animation = '', 500);
                return;
            }}

            // Disable button and show loading spinner
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner"></span>확인 중...';

            try {{
                // Call server API
                const response = await fetch('/problem/submit', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    credentials: 'include',  // Include cookies for session
                    body: JSON.stringify({{
                        problem_id: '{problem_data['problem_id']}',
                        user_answer: userAnswer
                    }})
                }});

                if (!response.ok) {{
                    throw new Error('서버 오류');
                }}

                const result = await response.json();
                console.log('[Viewer] Server response:', result);

                // Display result
                resultDiv.style.display = 'block';
                resultDiv.className = 'result ' + (result.is_correct ? 'correct' : 'wrong');

                let html = '';

                if (result.is_correct) {{
                    // Correct answer - show checkmark animation
                    html += '<div class="checkmark-circle"><div class="checkmark"></div></div>';
                    html += '<h2>✅ 정답입니다!</h2><p>획득 점수: +' + result.score + '점</p>';

                    // Trigger confetti animation
                    setTimeout(() => createConfetti(), 300);
                }} else {{
                    // Wrong answer - show with shake
                    html += '<h2>❌ 오답입니다</h2><p>정답: ' + result.correct_answer + '</p>';
                    setTimeout(() => {{
                        resultDiv.style.animation = 'shake 0.5s';
                        setTimeout(() => resultDiv.style.animation = '', 500);
                    }}, 100);
                }}

                // Add solution if available
                if (result.solution && result.solution !== '풀이가 준비되지 않았습니다.') {{
                    html += '<div class="solution-section">';
                    html += '<h3>풀이</h3>';
                    html += '<div class="math-content">' + result.solution + '</div>';
                    html += '</div>';
                }}

                // Show save status
                if (result.saved) {{
                    html += '<p style="margin-top: 10px; font-size: 12px; opacity: 0.8;">✓ 기록 저장됨</p>';
                }}

                resultDiv.innerHTML = html;

                // Render math in result (solution)
                if (window.renderMathInElement) {{
                    renderMathInElement(resultDiv, {{
                        delimiters: [
                            {{left: '$$', right: '$$', display: true}},
                            {{left: '$', right: '$', display: false}},
                            {{left: '\\\\(', right: '\\\\)', display: false}},
                            {{left: '\\\\[', right: '\\\\]', display: true}}
                        ],
                        throwOnError: false
                    }});
                }}

                // Scroll to result
                resultDiv.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});

                // Hide submit button with fade out
                submitBtn.style.transition = 'opacity 0.3s, transform 0.3s';
                submitBtn.style.opacity = '0';
                submitBtn.style.transform = 'translateY(10px)';
                setTimeout(() => submitBtn.style.display = 'none', 300);

            }} catch (error) {{
                console.error('[Viewer] Error:', error);
                // Show error with shake
                submitBtn.style.animation = 'shake 0.5s';
                setTimeout(() => submitBtn.style.animation = '', 500);

                resultDiv.style.display = 'block';
                resultDiv.className = 'result wrong';
                resultDiv.innerHTML = '<h2>⚠️ 오류 발생</h2><p>답안 제출 중 오류가 발생했습니다.<br>다시 시도해주세요.</p>';

                submitBtn.disabled = false;
                submitBtn.innerHTML = '정답 확인';
            }}
        }}

        function createConfetti() {{
            const colors = ['#ffd700', '#ff6b6b', '#4ecdc4', '#45b7d1', '#f7b731', '#5f27cd'];
            const confettiCount = 50;

            for (let i = 0; i < confettiCount; i++) {{
                const confetti = document.createElement('div');
                confetti.style.position = 'fixed';
                confetti.style.width = Math.random() * 10 + 5 + 'px';
                confetti.style.height = Math.random() * 10 + 5 + 'px';
                confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
                confetti.style.left = Math.random() * 100 + '%';
                confetti.style.top = '-10px';
                confetti.style.opacity = '1';
                confetti.style.borderRadius = Math.random() > 0.5 ? '50%' : '0';
                confetti.style.zIndex = '9999';
                confetti.style.pointerEvents = 'none';

                const duration = Math.random() * 3 + 2;
                const delay = Math.random() * 0.5;
                const rotation = Math.random() * 360;

                confetti.style.animation = `confettiFall ${{duration}}s ease-out ${{delay}}s forwards`;
                confetti.style.transform = `rotate(${{rotation}}deg)`;

                document.body.appendChild(confetti);

                setTimeout(() => confetti.remove(), (duration + delay) * 1000);
            }}
        }}

        let currentHintLevel = 0;
        const maxHintLevel = 3;

        async function requestHint() {{
            if (currentHintLevel >= maxHintLevel) {{
                return;
            }}

            const nextLevel = currentHintLevel + 1;
            const hintBtn = document.getElementById('hintBtn');
            const hintBtnText = document.getElementById('hintBtnText');
            const hintContainer = document.getElementById('hintContainer');

            // Disable button and show loading
            hintBtn.disabled = true;
            hintBtnText.textContent = '로딩 중...';

            try {{
                // Call backend to get hint
                const response = await fetch(`/problem/hint/${{nextLevel}}`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    credentials: 'include',
                    body: JSON.stringify({{
                        problem_id: '{problem_data['problem_id']}'
                    }})
                }});

                if (!response.ok) {{
                    const error = await response.json();
                    throw new Error(error.detail || '힌트를 불러올 수 없습니다');
                }}

                const result = await response.json();
                console.log('[Hint] Received hint:', result);

                // Check if hint is time-locked
                if (result.locked) {{
                    const lockedCard = document.createElement('div');
                    lockedCard.className = 'hint-card';
                    lockedCard.style.background = 'linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%)';
                    lockedCard.style.border = '2px dashed #9ca3af';
                    lockedCard.innerHTML = `
                        <h3>
                            <span class="hint-badge" style="background: linear-gradient(135deg, #9ca3af 0%, #6b7280 100%);">힌트 ${{nextLevel}}</span>
                            <span>&#128274;</span>
                        </h3>
                        <p style="color: #6b7280; font-weight: 500;">${{result.message}}</p>
                    `;
                    hintContainer.appendChild(lockedCard);
                    lockedCard.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});

                    // Keep button enabled but don't advance level
                    hintBtn.disabled = false;
                    hintBtnText.textContent = `힌트 ${{nextLevel}}단계 보기`;
                    return;
                }}

                // Display hint card
                const hintCard = document.createElement('div');
                hintCard.className = 'hint-card';
                hintCard.innerHTML = `
                    <h3>
                        <span class="hint-badge">힌트 ${{nextLevel}}</span>
                        <span>${{getHintIcon(nextLevel)}}</span>
                    </h3>
                    <p class="math-content">${{result.hint_text}}</p>
                `;
                hintContainer.appendChild(hintCard);

                // Render math in hint card
                if (window.renderMathInElement) {{
                    renderMathInElement(hintCard, {{
                        delimiters: [
                            {{left: '$$', right: '$$', display: true}},
                            {{left: '$', right: '$', display: false}},
                            {{left: '\\\\(', right: '\\\\)', display: false}},
                            {{left: '\\\\[', right: '\\\\]', display: true}}
                        ],
                        throwOnError: false
                    }});
                }}

                // Update current level
                currentHintLevel = nextLevel;

                // Update button
                hintBtn.disabled = false;
                if (currentHintLevel < maxHintLevel) {{
                    hintBtnText.textContent = `힌트 ${{currentHintLevel + 1}}단계 보기`;
                }} else {{
                    hintBtnText.textContent = '모든 힌트를 확인했습니다';
                    hintBtn.disabled = true;
                    hintBtn.style.background = 'linear-gradient(135deg, #9ca3af 0%, #6b7280 100%)';
                }}

                // Scroll to hint
                hintCard.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});

            }} catch (error) {{
                console.error('[Hint] Error:', error);
                alert(error.message || '힌트를 불러오는 중 오류가 발생했습니다.');
                hintBtn.disabled = false;
                hintBtnText.textContent = `힌트 ${{nextLevel}}단계 보기`;
            }}
        }}

        function getHintIcon(level) {{
            const icons = {{
                1: '🔍 개념 방향',
                2: '🔑 핵심 전환',
                3: '✨ 결정적 힌트'
            }};
            return icons[level] || '💡 힌트';
        }}
    </script>
</body>
</html>"""

    print(f"[Problem Viewer] Returning HTML ({len(html)} bytes)")
    return HTMLResponse(content=html)


class SubmitAnswerRequest(BaseModel):
    problem_id: str
    user_answer: str


class HintRequest(BaseModel):
    problem_id: str


@router.post("/submit")
async def submit_answer(request: Request, body: SubmitAnswerRequest):
    """
    Submit answer and check correctness (for problem viewer)
    Saves to user_problems and updates user statistics
    """
    # Get user from session (optional - viewer works without login)
    session_token = request.cookies.get("session_token")
    user = None
    if session_token:
        user_service = UserService()
        user = user_service.get_user_by_session(session_token)

    supabase = SupabaseService()
    problem = supabase.get_problem(body.problem_id)

    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    correct_answer = problem.get("answer_verified") or problem.get("answer")
    solution = problem.get("solution") or "풀이가 준비되지 않았습니다."

    # Check if answer is correct
    is_correct = str(body.user_answer).strip() == str(correct_answer).strip()
    score = problem.get("score", 3) if is_correct else 0

    print(f"[Submit Answer] problem={body.problem_id}, user_answer={body.user_answer}, correct={is_correct}")

    # Save attempt to database (if user is logged in)
    if user:
        try:
            # Save to user_problems table
            supabase.client.table("user_problems").insert({
                "user_id": user.get("id"),
                "problem_id": body.problem_id,
                "user_answer": body.user_answer,
                "is_correct": is_correct,
                "hint_used": 0,  # TODO: track hint usage
            }).execute()

            # Update user statistics
            current_correct = user.get("correct_count", 0)
            current_total = user.get("total_problems_solved", 0)
            consecutive_correct = user.get("consecutive_correct", 0)
            consecutive_wrong = user.get("consecutive_wrong", 0)

            if is_correct:
                consecutive_correct += 1
                consecutive_wrong = 0
            else:
                consecutive_correct = 0
                consecutive_wrong += 1

            supabase.client.table("users").update({
                "total_problems_solved": current_total + 1,
                "correct_count": current_correct + (1 if is_correct else 0),
                "consecutive_correct": consecutive_correct,
                "consecutive_wrong": consecutive_wrong,
                "updated_at": "now()"
            }).eq("id", user.get("id")).execute()

            print(f"[Submit Answer] Saved to database for user {user.get('kakao_id')}")

        except Exception as e:
            print(f"[Submit Answer] Error saving to database: {e}")
            # Continue anyway - don't fail the submission

    return {
        "is_correct": is_correct,
        "correct_answer": correct_answer,
        "solution": solution,
        "score": score,
        "saved": user is not None
    }


@router.post("/hint/{level}")
async def get_hint(request: Request, level: int, body: HintRequest):
    """
    Get hint for a problem (for problem viewer).
    Progressive hints: level 1, 2, or 3.

    Time-based unlock (if published_at is set):
      - Hint 1: available immediately at published_at
      - Hint 2: published_at + hint_interval_hours
      - Hint 3 + solution: published_at + hint_interval_hours * 2
    If published_at is NULL, all hints are available immediately.
    """
    if level not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="Hint level must be 1, 2, or 3")

    supabase = SupabaseService()

    # ── Time-based unlock check ──
    try:
        problem_result = supabase.client.table("problems") \
            .select("published_at, hint_interval_hours") \
            .eq("problem_id", body.problem_id) \
            .single() \
            .execute()

        if problem_result.data:
            published_at = problem_result.data.get("published_at")
            if published_at and level > 1:
                from datetime import datetime, timedelta, timezone
                if isinstance(published_at, str):
                    published = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                else:
                    published = published_at
                if published.tzinfo is None:
                    published = published.replace(tzinfo=timezone.utc)

                interval = problem_result.data.get("hint_interval_hours", 24) or 24
                unlock_at = published + timedelta(hours=interval * (level - 1))
                now = datetime.now(timezone.utc)

                if now < unlock_at:
                    remaining = unlock_at - now
                    hours_left = int(remaining.total_seconds() // 3600)
                    mins_left = int((remaining.total_seconds() % 3600) // 60)
                    time_msg = f"{hours_left}시간 {mins_left}분 후" if hours_left > 0 else f"{mins_left}분 후"

                    print(f"[Get Hint] LOCKED: problem={body.problem_id}, level={level}, unlocks in {time_msg}")
                    return {
                        "locked": True,
                        "level": level,
                        "unlock_at": unlock_at.isoformat(),
                        "message": f"힌트 {level}단계는 {time_msg} 공개됩니다."
                    }
    except Exception:
        pass  # Column may not exist yet — skip time check, allow all hints

    # ── Get hint from hints table ──
    try:
        result = supabase.client.table("hints") \
            .select("hint_text, hint_type, stage") \
            .eq("problem_id", body.problem_id) \
            .eq("stage", level) \
            .single() \
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail=f"Hint {level} not available for this problem")

        hint_data = result.data
        print(f"[Get Hint] problem={body.problem_id}, level={level}, hint={hint_data.get('hint_text')[:50]}...")

        # Track hint request (optional - if user is logged in)
        session_token = request.cookies.get("session_token")
        if session_token:
            user_service = UserService()
            user = user_service.get_user_by_session(session_token)
            if user:
                try:
                    supabase.client.table("hint_requests").insert({
                        "user_id": user.get("id"),
                        "problem_id": body.problem_id,
                        "hint_level": level,
                    }).execute()
                    print(f"[Get Hint] Tracked hint request for user {user.get('kakao_id')}")
                except Exception as e:
                    print(f"[Get Hint] Error tracking hint request: {e}")

        return {
            "locked": False,
            "hint_text": hint_data.get("hint_text"),
            "hint_type": hint_data.get("hint_type"),
            "level": level
        }

    except Exception as e:
        print(f"[Get Hint] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get hint: {str(e)}")

