# utils/session_manager.py
import os
import pickle
import time
import shutil
from pathlib import Path
from core.config import COOKIE_STORAGE_DIR, BROWSER_PROFILES_DIR, SESSION_MAX_AGE_HOURS

class SessionManager:
    def __init__(self):
        self.cookie_storage_dir = COOKIE_STORAGE_DIR
        self.browser_profiles_dir = BROWSER_PROFILES_DIR

    def get_browser_profile_dir(self, session_id):
        """Get browser profile directory for this session"""
        if session_id:
            profile_dir = self.browser_profiles_dir / session_id
            os.makedirs(profile_dir, exist_ok=True)
            print(f"🔧 DEBUG: Browser profile directory: {profile_dir}")
            return str(profile_dir)
        return None

    def get_cookie_file(self, session_id):
        """Get cookie file path for this session"""
        if session_id:
            cookie_file = self.cookie_storage_dir / f"{session_id}.pkl"
            print(f"🔧 DEBUG: Cookie file path: {cookie_file}")
            return cookie_file
        return None

    async def save_cookies(self, context, session_id):
        """Save cookies for this session"""
        print(f"💾 DEBUG: save_cookies called with session_id: {session_id}")
        if session_id:
            cookies = await context.cookies()
            cookie_file = self.get_cookie_file(session_id)
            
            print(f"💾 DEBUG: Saving {len(cookies)} cookies to: {cookie_file}")
            with open(str(cookie_file), 'wb') as f:
                pickle.dump(cookies, f)
            
            print(f"✅ Cookies saved. File exists: {os.path.exists(cookie_file)}")
        else:
            print("❌ No session_id provided to save_cookies")

    async def load_cookies(self, context, session_id):
        """Load cookies for this session"""
        print(f"🔄 DEBUG: load_cookies called with session_id: {session_id}")
        if session_id:
            cookie_file = self.get_cookie_file(session_id)
            print(f"🔄 DEBUG: Cookie file path: {cookie_file}")
            print(f"🔄 DEBUG: Cookie file exists: {os.path.exists(cookie_file)}")
            
            if cookie_file is not None and os.path.exists(cookie_file):
                print(f"🔄 DEBUG: Loading cookies from: {cookie_file}")
                with open(cookie_file, 'rb') as f:
                    cookies = pickle.load(f)
                
                print(f"🔄 DEBUG: Loaded {len(cookies)} cookies")
                await context.add_cookies(cookies)
                print("✅ Cookies loaded successfully")
                return True
            else:
                print("❌ No cookie file found or session_id missing")
        return False

    async def validate_session(self, session_id):
        """Check if a session has valid cookies"""
        if not session_id:
            return False
        
        cookie_file = self.get_cookie_file(session_id)
        if not os.path.exists(cookie_file):
            print(f"❌ Session validation failed: No cookie file for {session_id}")
            return False
        
        try:
            with open(cookie_file, 'rb') as f:
                cookies = pickle.load(f)
            
            # Check if we have LinkedIn auth cookies
            linkedin_cookies = [c for c in cookies if 'linkedin' in c.get('domain', '')]
            print(f"🔍 Session {session_id} has {len(linkedin_cookies)} LinkedIn cookies")
            
            return len(linkedin_cookies) > 0
        except Exception as e:
            print(f"❌ Session validation error: {e}")
            return False

    async def clear_session_data(self, session_id):
        """Clear all data for a session"""
        try:
            # Remove cookie file
            cookie_file = self.get_cookie_file(session_id)
            if cookie_file and os.path.exists(cookie_file):
                os.remove(cookie_file)
                print(f"🗑️ Removed cookie file: {cookie_file}")
            
            # Remove browser profile
            profile_dir = self.get_browser_profile_dir(session_id)
            if profile_dir and os.path.exists(profile_dir):
                shutil.rmtree(profile_dir)
                print(f"🗑️ Removed browser profile: {profile_dir}")
                
        except Exception as e:
            print(f"❌ Error clearing session data: {e}")

    async def cleanup_old_sessions(self):
        """Remove sessions older than SESSION_MAX_AGE_HOURS"""
        current_time = time.time()
        max_age_seconds = SESSION_MAX_AGE_HOURS * 3600
        
        print("🧹 Checking for old sessions to cleanup...")
        
        # FIX: Changed cookie_files to cookie_storage_dir
        for cookie_file in self.cookie_storage_dir.glob("*.pkl"):
            if (current_time - cookie_file.stat().st_mtime) > max_age_seconds:
                session_id = cookie_file.stem
                print(f"🧹 Removing expired session: {session_id}")
                await self.clear_session_data(session_id)
        
        # Cleanup old browser profiles
        for profile_dir in self.browser_profiles_dir.iterdir():
            if profile_dir.is_dir() and (current_time - profile_dir.stat().st_mtime) > max_age_seconds:
                print(f"🧹 Removing expired browser profile: {profile_dir.name}")
                shutil.rmtree(profile_dir)

# Singleton instance
session_manager = SessionManager()