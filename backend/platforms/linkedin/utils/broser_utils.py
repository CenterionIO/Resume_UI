# utils/browser_utils.py
import asyncio
import random
from playwright.async_api import async_playwright # type: ignore
from core.config import BROWSER_CONFIG
from utils.session_manager import session_manager

class BrowserUtils:
    def __init__(self):
        self.browser_config = BROWSER_CONFIG

    async def wait_for_random_delay(self, min_seconds=1, max_seconds=3):
        """Wait for a random delay to simulate human behavior"""
        await asyncio.sleep(random.uniform(min_seconds, max_seconds))

    async def scroll_to_bottom(self, page):
        """Scroll like a human with variable speed"""
        viewport_height = await page.evaluate("window.innerHeight")
        scroll_height = await page.evaluate("document.body.scrollHeight")
        
        current_position = 0
        while current_position < scroll_height:
            scroll_amount = random.randint(100, 300)
            current_position += scroll_amount
            await page.evaluate(f"window.scrollTo(0, {current_position})")
            await asyncio.sleep(random.uniform(0.1, 0.5))

    async def wait_for_linkedin_load(self, page, timeout=30000):
        """Wait for LinkedIn to load sufficiently without strict networkidle"""
        try:
            # Wait for main content to appear
            await page.wait_for_selector(".scaffold-layout__main, .jobs-description__content, .feed-identity-module", 
                                       timeout=timeout)
            print("✅ LinkedIn main content loaded")
        except Exception as e:
            print(f"⚠️ Content loading slow, but continuing: {e}")
        
        # Wait a bit more for any additional loading
        await self.wait_for_random_delay(2, 3)

    async def create_browser_context(self, session_id=None):
        """Create browser context with session persistence"""
        print(f"🔧 DEBUG: create_browser_context called with session_id: {session_id}")
        
        # Run cleanup on startup
        await session_manager.cleanup_old_sessions()
        
        p = await async_playwright().start()
        
        if session_id:
            # Use persistent profile for this session
            profile_dir = session_manager.get_browser_profile_dir(session_id)
            print(f"🔧 DEBUG: Creating persistent context with profile: {profile_dir}")
            
            context = await p.chromium.launch_persistent_context(
                user_data_dir=profile_dir,
                headless=False,
                **self.browser_config
            )
            print(f"🔧 DEBUG: Persistent context created for session: {session_id}")
        else:
            print("🔧 DEBUG: Creating temporary browser context (no session_id)")
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(**self.browser_config)
        
        return p, context

# Singleton instance
browser_utils = BrowserUtils()