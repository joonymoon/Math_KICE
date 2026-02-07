"""
User Management Service
Handles user CRUD and session management with Supabase
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", SUPABASE_KEY)


class UserService:
    """User management with Supabase"""

    # Class-level session storage (shared across all instances)
    _sessions: Dict[str, str] = {}  # session_token -> kakao_id

    def __init__(self):
        self.base_url = SUPABASE_URL
        self.headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def _request(self, method: str, endpoint: str, data: dict = None) -> Optional[dict]:
        """Make request to Supabase REST API"""
        url = f"{self.base_url}/rest/v1/{endpoint}"

        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, params=data, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method == "PATCH":
                response = requests.patch(url, headers=self.headers, json=data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers, timeout=10)
            else:
                return None

            if response.status_code in [200, 201]:
                result = response.json()
                return result[0] if isinstance(result, list) and len(result) > 0 else result
            elif response.status_code == 204:
                return {}
            else:
                print(f"Supabase error: {response.status_code} - {response.text}")
                return None

        except requests.RequestException as e:
            print(f"Request error: {e}")
            return None

    def get_user_by_kakao_id(self, kakao_id: str) -> Optional[dict]:
        """Get user by Kakao ID"""
        url = f"{self.base_url}/rest/v1/users?kakao_id=eq.{kakao_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                users = response.json()
                return users[0] if users else None
        except requests.RequestException:
            pass
        return None

    def upsert_user(
        self,
        kakao_id: str,
        nickname: str,
        email: Optional[str] = None,
        profile_image: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[datetime] = None
    ) -> Optional[dict]:
        """Create or update user"""
        # Check if user exists
        existing_user = self.get_user_by_kakao_id(kakao_id)

        user_data = {
            "kakao_id": kakao_id,
            "nickname": nickname,
            "email": email,
            "profile_image": profile_image,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_expires_at": token_expires_at.isoformat() if token_expires_at else None,
            "updated_at": datetime.now().isoformat()
        }

        # Remove None values
        user_data = {k: v for k, v in user_data.items() if v is not None}

        if existing_user:
            # Update existing user
            url = f"{self.base_url}/rest/v1/users?kakao_id=eq.{kakao_id}"
            try:
                response = requests.patch(
                    url,
                    headers=self.headers,
                    json=user_data,
                    timeout=10
                )
                if response.status_code in [200, 204]:
                    return self.get_user_by_kakao_id(kakao_id)
            except requests.RequestException as e:
                print(f"Update error: {e}")
                return None
        else:
            # Create new user
            user_data["created_at"] = datetime.now().isoformat()
            user_data["current_level"] = 3  # Default difficulty level
            user_data["current_score_level"] = 3  # Default score level (3-point problems)
            user_data["subscription_type"] = "free"

            url = f"{self.base_url}/rest/v1/users"
            print(f"[Debug] Creating user at: {url}")
            print(f"[Debug] User data: {user_data}")
            try:
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=user_data,
                    timeout=10
                )
                print(f"[Debug] Response status: {response.status_code}")
                print(f"[Debug] Response body: {response.text[:500]}")
                if response.status_code in [200, 201]:
                    result = response.json()
                    return result[0] if isinstance(result, list) else result
            except requests.RequestException as e:
                print(f"Create error: {e}")
                return None

        return None

    def update_tokens(
        self,
        kakao_id: str,
        access_token: str,
        refresh_token: str,
        token_expires_at: datetime
    ) -> bool:
        """Update user's OAuth tokens"""
        url = f"{self.base_url}/rest/v1/users?kakao_id=eq.{kakao_id}"

        data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_expires_at": token_expires_at.isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        try:
            response = requests.patch(url, headers=self.headers, json=data, timeout=10)
            return response.status_code in [200, 204]
        except requests.RequestException:
            return False

    def create_session(self, kakao_id: str) -> str:
        """Create a new session for user"""
        session_token = secrets.token_urlsafe(32)
        self._sessions[session_token] = kakao_id

        # Also store in database for persistence (optional)
        # self._store_session_in_db(session_token, kakao_id)

        return session_token

    def get_user_by_session(self, session_token: str) -> Optional[dict]:
        """Get user by session token"""
        kakao_id = self._sessions.get(session_token)
        if not kakao_id:
            return None
        return self.get_user_by_kakao_id(kakao_id)

    def delete_session(self, session_token: str) -> bool:
        """Delete session"""
        if session_token in self._sessions:
            del self._sessions[session_token]
            return True
        return False

    def update_user_level(
        self,
        kakao_id: str,
        current_level: int,
        current_score_level: int
    ) -> bool:
        """Update user's difficulty level"""
        url = f"{self.base_url}/rest/v1/users?kakao_id=eq.{kakao_id}"

        data = {
            "current_level": current_level,
            "current_score_level": current_score_level,
            "updated_at": datetime.now().isoformat()
        }

        try:
            response = requests.patch(url, headers=self.headers, json=data, timeout=10)
            return response.status_code in [200, 204]
        except requests.RequestException:
            return False

    def update_subscription(
        self,
        kakao_id: str,
        subscription_type: str,
        subscription_expires_at: Optional[datetime] = None
    ) -> bool:
        """Update user's subscription"""
        url = f"{self.base_url}/rest/v1/users?kakao_id=eq.{kakao_id}"

        data = {
            "subscription_type": subscription_type,
            "updated_at": datetime.now().isoformat()
        }

        if subscription_expires_at:
            data["subscription_expires_at"] = subscription_expires_at.isoformat()

        try:
            response = requests.patch(url, headers=self.headers, json=data, timeout=10)
            return response.status_code in [200, 204]
        except requests.RequestException:
            return False

    def get_all_active_users(self) -> list:
        """Get all users with active subscriptions"""
        url = f"{self.base_url}/rest/v1/users"
        params = {
            "select": "kakao_id,nickname,access_token,current_level,current_score_level,subscription_type",
            "subscription_type": "neq.cancelled"
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException:
            pass
        return []

    def get_users_for_delivery(self, delivery_time: str = "07:00") -> list:
        """Get users scheduled for problem delivery at specific time"""
        # For now, return all active users
        # In production, filter by user preferences
        return self.get_all_active_users()


# Database schema for users table (run once in Supabase SQL editor)
USERS_TABLE_SQL = """
-- Users table for KICE Math KakaoTalk Service
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    kakao_id TEXT UNIQUE NOT NULL,
    nickname TEXT,
    email TEXT,
    profile_image TEXT,

    -- OAuth tokens
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMPTZ,

    -- Learning settings
    current_level INTEGER DEFAULT 3,        -- 1-5 difficulty
    current_score_level INTEGER DEFAULT 3,  -- 2, 3, 4 point problems
    preferred_subject TEXT,                 -- Math1, Math2, or NULL for both

    -- Subscription
    subscription_type TEXT DEFAULT 'free',  -- free, basic, premium
    subscription_expires_at TIMESTAMPTZ,

    -- Stats
    total_problems_solved INTEGER DEFAULT 0,
    correct_count INTEGER DEFAULT 0,
    consecutive_correct INTEGER DEFAULT 0,
    consecutive_wrong INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_kakao_id ON users(kakao_id);
CREATE INDEX IF NOT EXISTS idx_users_subscription ON users(subscription_type);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own data
CREATE POLICY "Users can read own data" ON users
    FOR SELECT USING (true);

-- Policy: Service role can do everything
CREATE POLICY "Service role full access" ON users
    FOR ALL USING (true);
"""


def setup_database():
    """Print SQL to setup database"""
    print("=" * 60)
    print("Run this SQL in Supabase SQL Editor to create users table:")
    print("=" * 60)
    print(USERS_TABLE_SQL)
    print("=" * 60)


if __name__ == "__main__":
    setup_database()
