# utils/session_manager.py
import os
import pickle
import time
import shutil
from pathlib import Path

# Point to browser/storage
BROWSER_ROOT = Path(__file__).parent.parent  # Go up to browser/
COOKIE_STORAGE_DIR = BROWSER_ROOT / "storage" / "cookies"
BROWSER_PROFILES_DIR = BROWSER_ROOT / "storage" / "profiles"
SESSION_MAX_AGE_HOURS = 336

os.makedirs(COOKIE_STORAGE_DIR, exist_ok=True)
os.makedirs(BROWSER_PROFILES_DIR, exist_ok=True)

class SessionManager:
    def __init__(self):
        self.cookie_storage_dir = COOKIE_STORAGE_DIR
        self.browser_profiles_dir = BROWSER_PROFILES_DIR
        print(f"🔧 SessionManager initialized")

    def get_browser_profile_dir(self, session_id):
        if session_id:
            profile_dir = self.browser_profiles_dir / session_id
            os.makedirs(profile_dir, exist_ok=True)
            return str(profile_dir)
        return None

    def get_cookie_file(self, session_id):
        if session_id:
            return self.cookie_storage_dir / f"{session_id}.pkl"
        return None

    async def save_cookies(self, context, session_id):
        print(f"💾 Saving cookies for session: {session_id}")
        if session_id:
            cookies = await context.cookies()
            cookie_file = self.get_cookie_file(session_id)
            
            with open(str(cookie_file), 'wb') as f:
                pickle.dump(cookies, f)
            
            print(f"✅ Cookies saved: {len(cookies)} cookies")
            return True
        return False

    async def load_cookies(self, context, session_id):
        print(f"🔄 Loading cookies for session: {session_id}")
        if session_id:
            cookie_file = self.get_cookie_file(session_id)
            
            if cookie_file and os.path.exists(cookie_file):
                with open(cookie_file, 'rb') as f:
                    cookies = pickle.load(f)
                
                await context.clear_cookies()
                await context.add_cookies(cookies)
                print(f"✅ Cookies loaded: {len(cookies)} cookies")
                return True
        print("❌ No cookies to load")
        return False

    async def validate_session(self, session_id):
        """Check if session has valid LinkedIn cookies"""
        if not session_id:
            return False
        
        cookie_file = self.get_cookie_file(session_id)
        if not cookie_file or not os.path.exists(cookie_file):
            print(f"❌ No cookie file for session: {session_id}")
            return False
        
        try:
            with open(cookie_file, 'rb') as f:
                cookies = pickle.load(f)
            
            # Check for LinkedIn authentication cookies
            linkedin_auth_cookies = [
                c for c in cookies 
                if 'linkedin.com' in c.get('domain', '') 
                and c.get('name') in ['li_at', 'JSESSIONID', 'bcookie']
            ]
            
            has_valid_cookies = len(linkedin_auth_cookies) >= 2
            print(f"🔍 Session {session_id} has {len(linkedin_auth_cookies)} auth cookies - Valid: {has_valid_cookies}")
            
            return has_valid_cookies
        except Exception as e:
            print(f"❌ Session validation error: {e}")
            return False

    async def clear_session_data(self, session_id):
        try:
            print(f"🗑️ Clearing session: {session_id}")
            cookie_file = self.get_cookie_file(session_id)
            if cookie_file and os.path.exists(cookie_file):
                os.remove(cookie_file)
            
            profile_dir = self.get_browser_profile_dir(session_id)
            if profile_dir and os.path.exists(profile_dir):
                shutil.rmtree(profile_dir)
        except Exception as e:
            print(f"❌ Error clearing session: {e}")

    async def cleanup_old_sessions(self):
        current_time = time.time()
        max_age_seconds = SESSION_MAX_AGE_HOURS * 3600
        
        print("🧹 Cleaning up old sessions...")
        for cookie_file in self.cookie_storage_dir.glob("*.pkl"):
            if (current_time - cookie_file.stat().st_mtime) > max_age_seconds:
                session_id = cookie_file.stem
                print(f"🧹 Removing expired session: {session_id}")
                await self.clear_session_data(session_id)

session_manager = SessionManager()