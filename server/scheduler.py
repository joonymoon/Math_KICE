"""
Daily Problem Scheduler
Automatically sends math problems to users via KakaoTalk at their preferred time.
Includes automatic token refresh and adaptive problem selection.

Usage:
    # Run as standalone scheduler
    python -m server.scheduler

    # Or integrate with FastAPI via run.py --send-daily
"""

import os
import sys
import time
import random
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Optional

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.supabase_service import SupabaseService
from server.kakao_message import KakaoMessageService

# Kakao OAuth config
KAKAO_CLIENT_ID = os.getenv("KAKAO_REST_API_KEY", "")
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"


class DailyScheduler:
    """Manages daily problem delivery to users with adaptive selection and token refresh"""

    def __init__(self):
        self.supabase = SupabaseService()
        self.messenger = KakaoMessageService()
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")

    # ===== Token Management =====

    def get_active_users(self) -> List[Dict]:
        """Get all active users with valid Kakao tokens"""
        result = self.supabase.client.table("users").select(
            "id, kakao_id, nickname, access_token, refresh_token, "
            "token_expires_at, current_level, current_score_level"
        ).execute()

        # Filter users with valid tokens (access or refresh)
        users = [u for u in result.data if u.get("access_token") or u.get("refresh_token")]
        return users

    def refresh_token_if_needed(self, user: Dict) -> Optional[str]:
        """Check token expiry and refresh if needed. Returns valid access_token or None."""
        access_token = user.get("access_token")
        refresh_token = user.get("refresh_token")
        expires_at = user.get("token_expires_at")

        # Check if token is expired or will expire within 10 minutes
        if expires_at:
            try:
                exp_time = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                if exp_time.tzinfo:
                    from datetime import timezone
                    now = datetime.now(timezone.utc)
                else:
                    now = datetime.now()
                if now + timedelta(minutes=10) < exp_time:
                    return access_token  # Still valid
            except (ValueError, TypeError):
                pass  # Can't parse, try refresh

        # Token expired or unknown expiry - try to refresh
        if not refresh_token:
            return access_token  # No refresh token, return what we have

        if not KAKAO_CLIENT_ID:
            print(f"  Warning: KAKAO_REST_API_KEY not set, can't refresh token")
            return access_token

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

            if response.status_code == 200:
                token_data = response.json()
                new_access_token = token_data.get("access_token")
                new_refresh_token = token_data.get("refresh_token", refresh_token)
                expires_in = token_data.get("expires_in", 21600)

                # Update DB
                new_expires_at = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
                self.supabase.client.table("users").update({
                    "access_token": new_access_token,
                    "refresh_token": new_refresh_token,
                    "token_expires_at": new_expires_at,
                    "updated_at": datetime.now().isoformat(),
                }).eq("id", user["id"]).execute()

                nickname = user.get("nickname", "?")
                print(f"  Token refreshed for {nickname} (expires in {expires_in}s)")
                return new_access_token
            else:
                print(f"  Token refresh failed: {response.status_code} {response.text[:100]}")
                return access_token

        except requests.RequestException as e:
            print(f"  Token refresh error: {e}")
            return access_token

    # ===== Adaptive Problem Selection =====

    def get_adaptive_problem(self, user: Dict) -> Optional[Dict]:
        """Use recommend_next_problem() SQL function for adaptive selection"""
        user_id = user["id"]
        try:
            result = self.supabase.client.rpc(
                "recommend_next_problem",
                {"p_user_id": user_id}
            ).execute()

            if result.data and len(result.data) > 0:
                rec = result.data[0]
                # Fetch full problem data
                problem = self.supabase.client.table("problems").select(
                    "problem_id, year, exam, question_no, score, unit, subject, "
                    "problem_image_url, answer_verified, answer"
                ).eq("problem_id", rec["problem_id"]).execute()

                if problem.data:
                    p = problem.data[0]
                    p["_recommendation_reason"] = rec.get("recommendation_reason", "")
                    return p
        except Exception as e:
            print(f"  Adaptive selection failed: {e}, falling back to sequential")

        # Fallback: get unsent problems sequentially
        problems = self.get_unsent_problems(user_id)
        return problems[0] if problems else None

    def get_unsent_problems(self, user_id: str, count: int = 1) -> List[Dict]:
        """Get problems that haven't been sent to this user yet (fallback)"""
        # Get already delivered problem IDs for this user
        delivered = self.supabase.client.table("deliveries").select(
            "problem_id"
        ).eq("user_id", user_id).execute()

        delivered_ids = [d["problem_id"] for d in delivered.data]

        # Get ready problems not yet delivered
        query = self.supabase.client.table("problems").select(
            "problem_id, year, exam, question_no, score, unit, subject, "
            "problem_image_url, answer_verified, answer"
        ).eq("status", "ready")

        if delivered_ids:
            query = query.not_.in_("problem_id", delivered_ids)

        result = query.order("year", desc=True).order("question_no").limit(count).execute()
        return result.data

    def create_daily_schedule(self, user: Dict, target_date: date = None) -> Optional[Dict]:
        """Create a daily schedule entry for a user"""
        target_date = target_date or date.today()
        preferred_time = user.get("preferred_time", "07:00")
        count = user.get("daily_problem_count", 1)

        # Check if schedule already exists for today
        existing = self.supabase.client.table("daily_schedules").select(
            "id"
        ).eq("user_id", user["id"]).eq(
            "scheduled_date", target_date.isoformat()
        ).execute()

        if existing.data:
            return None  # Already scheduled

        # Get adaptive problem recommendation
        problem = self.get_adaptive_problem(user)
        if not problem:
            print(f"  No unsent problems for user {user.get('nickname', user['id'])}")
            return None

        reason = problem.pop("_recommendation_reason", "sequential")

        # Create schedule
        schedule_data = {
            "scheduled_date": target_date.isoformat(),
            "user_id": user["id"],
            "problem_id": problem["problem_id"],
            "scheduled_time": preferred_time,
            "status": "scheduled",
        }

        try:
            result = self.supabase.client.table("daily_schedules").upsert(
                schedule_data,
                on_conflict="scheduled_date,user_id"
            ).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"  Schedule creation error: {e}")
            return None

    def execute_pending_schedules(self) -> Dict:
        """Execute all pending schedules that are due"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        today = date.today().isoformat()

        print(f"\n[Scheduler] Checking pending schedules at {now.strftime('%H:%M:%S')}")

        # Get pending schedules for today where time has passed
        result = self.supabase.client.table("daily_schedules").select(
            "*, users!inner(access_token, refresh_token, token_expires_at, nickname)"
        ).eq("status", "scheduled").eq("scheduled_date", today).lte(
            "scheduled_time", current_time
        ).execute()

        schedules = result.data
        stats = {"total": len(schedules), "sent": 0, "failed": 0, "skipped": 0}

        if not schedules:
            print("  No pending schedules")
            return stats

        print(f"  Found {len(schedules)} pending schedule(s)")

        for schedule in schedules:
            success = self._send_scheduled_problem(schedule)
            if success:
                stats["sent"] += 1
            else:
                stats["failed"] += 1

        print(f"  Results: {stats['sent']} sent, {stats['failed']} failed")
        return stats

    def _send_scheduled_problem(self, schedule: Dict) -> bool:
        """Send a single scheduled problem with automatic token refresh"""
        problem_id = schedule["problem_id"]
        user_data = schedule.get("users", {})
        nickname = user_data.get("nickname", "User")
        hint_delay = 30

        # Auto-refresh token if needed
        user_for_refresh = {
            "id": schedule["user_id"],
            "access_token": user_data.get("access_token"),
            "refresh_token": user_data.get("refresh_token"),
            "token_expires_at": user_data.get("token_expires_at"),
            "nickname": nickname,
        }
        access_token = self.refresh_token_if_needed(user_for_refresh)

        if not access_token:
            print(f"  Skip {problem_id}: no access token for {nickname}")
            self._update_schedule_status(schedule["id"], "failed", "No access token")
            return False

        # Get problem data
        problem_result = self.supabase.client.table("problems").select("*").eq(
            "problem_id", problem_id
        ).execute()

        if not problem_result.data:
            self._update_schedule_status(schedule["id"], "failed", "Problem not found")
            return False

        problem = problem_result.data[0]
        image_url = problem.get("problem_image_url") or problem.get("image_url")

        # Build viewer URL
        viewer_url = f"{self.base_url}/problem/view/{problem_id}"

        # Send via KakaoTalk
        try:
            result = self.messenger.send_math_problem(
                access_token=access_token,
                problem_id=problem_id,
                problem_text=f"{problem.get('year', '')} {problem.get('exam', '')} Q{problem.get('question_no', '')}",
                problem_image_url=image_url,
                year=problem.get("year"),
                exam=problem.get("exam"),
                number=problem.get("question_no"),
                difficulty=f"{problem.get('score', 3)}점",
                unit=problem.get("unit"),
                button_title="문제 풀기",
                button_url=viewer_url,
            )

            if result.get("success"):
                # Update schedule
                self._update_schedule_status(schedule["id"], "sent")

                # Create delivery record
                hint_available = datetime.now() + timedelta(minutes=hint_delay)
                self.supabase.client.table("deliveries").insert({
                    "user_id": schedule["user_id"],
                    "problem_id": problem_id,
                    "delivery_method": "kakao",
                    "hint_available_at": hint_available.isoformat(),
                    "kakao_send_result": result,
                    "status": "pending",
                }).execute()

                print(f"  Sent {problem_id} to {nickname}")
                return True
            else:
                error_msg = str(result.get("error", "Unknown"))[:200]
                self._update_schedule_status(schedule["id"], "failed", error_msg)
                print(f"  Failed {problem_id} to {nickname}: {error_msg}")
                return False

        except Exception as e:
            self._update_schedule_status(schedule["id"], "failed", str(e)[:200])
            print(f"  Error sending {problem_id}: {e}")
            return False

    def _update_schedule_status(self, schedule_id: str, status: str, error: str = None):
        """Update schedule status"""
        update = {"status": status, "executed_at": datetime.now().isoformat()}
        if error:
            update["error_message"] = error
        self.supabase.client.table("daily_schedules").update(update).eq(
            "id", schedule_id
        ).execute()

    def create_all_daily_schedules(self, target_date: date = None) -> int:
        """Create daily schedules for all active users"""
        target_date = target_date or date.today()
        users = self.get_active_users()
        created = 0

        print(f"\n[Scheduler] Creating schedules for {target_date} ({len(users)} active users)")

        for user in users:
            result = self.create_daily_schedule(user, target_date)
            if result:
                created += 1
                pid = result.get('problem_id', '?')
                print(f"  Scheduled for {user.get('nickname', 'Unknown')}: {pid}")

        print(f"  Created {created} new schedule(s)")
        return created

    def run_once(self):
        """Run one cycle: create schedules + execute pending"""
        print(f"\n{'='*50}")
        print(f"[Scheduler] Run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")

        # Step 1: Create schedules for today
        self.create_all_daily_schedules()

        # Step 2: Execute pending schedules
        stats = self.execute_pending_schedules()

        return stats

    def run_loop(self, check_interval_minutes: int = 5):
        """Run scheduler in a loop, checking every N minutes"""
        print(f"\n{'='*60}")
        print(f"  KICE Math Daily Scheduler")
        print(f"  Check interval: {check_interval_minutes} minutes")
        print(f"  Base URL: {self.base_url}")
        print(f"{'='*60}")

        while True:
            try:
                self.run_once()
            except Exception as e:
                print(f"[Scheduler Error] {e}")
                import traceback
                traceback.print_exc()

            print(f"\nNext check in {check_interval_minutes} minutes...")
            time.sleep(check_interval_minutes * 60)


# FastAPI router for scheduler endpoints
from fastapi import APIRouter, Request
scheduler_router = APIRouter()


@scheduler_router.post("/create-daily")
async def create_daily_schedules(request: Request):
    """Manually trigger daily schedule creation"""
    sched = DailyScheduler()
    created = sched.create_all_daily_schedules()
    return {"created": created, "date": date.today().isoformat()}


@scheduler_router.post("/execute")
async def execute_schedules(request: Request):
    """Manually trigger pending schedule execution"""
    sched = DailyScheduler()
    stats = sched.execute_pending_schedules()
    return stats


@scheduler_router.get("/status")
async def schedule_status(request: Request):
    """Get today's schedule status"""
    supabase = SupabaseService()
    today = date.today().isoformat()

    result = supabase.client.table("daily_schedules").select(
        "problem_id, status, scheduled_time, executed_at, error_message"
    ).eq("scheduled_date", today).execute()

    return {
        "date": today,
        "total": len(result.data),
        "scheduled": sum(1 for s in result.data if s["status"] == "scheduled"),
        "sent": sum(1 for s in result.data if s["status"] == "sent"),
        "failed": sum(1 for s in result.data if s["status"] == "failed"),
        "schedules": result.data,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="KICE Math Daily Scheduler")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=5, help="Check interval in minutes")
    parser.add_argument("--create-only", action="store_true", help="Only create schedules, don't send")

    args = parser.parse_args()

    scheduler = DailyScheduler()

    if args.create_only:
        scheduler.create_all_daily_schedules()
    elif args.once:
        scheduler.run_once()
    else:
        scheduler.run_loop(check_interval_minutes=args.interval)
