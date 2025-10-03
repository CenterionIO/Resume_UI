# modules/scraping/platforms/linkedin.py
import asyncio
import json
import re
from playwright.async_api import Page # type: ignore
from modules.auth.auth_manager import auth_manager                              
from utils.session_manager import session_manager
from utils.browser_utils import browser_utils
from modules.scraping.content_extractor import content_extractor

class LinkedInScraper:
    def __init__(self):
        self.platform_name = "linkedin"

    async def quick_login_check(self, page: Page) -> bool:
        """Fast login status check - like original version"""
        try:
            # Quick check for logged-in indicators
            if "feed" in page.url or "linkedin.com/feed" in page.url:
                return True
                
            logged_in = await page.query_selector(".global-nav__me, .nav-item__profile, [data-test-global-nav-link='Me']")
            return logged_in is not None
        except:
            return False

    async def fast_ensure_logged_in(self, page: Page, context, session_id: str, websocket=None):
        """Optimized login flow - similar to original speed"""
        async def send_update(message):
            if websocket:
                await websocket.send_text(json.dumps({"message": message}))
            print(message)

        # FAST PATH: Try quick cookie load and check
        cookies_loaded = await session_manager.load_cookies(context, session_id)
        
        if cookies_loaded:
            await page.goto("https://www.linkedin.com/feed", wait_until="domcontentloaded", timeout=10000)
            if await self.quick_login_check(page):
                await send_update("✅ Using existing session")
                return True

        # FAST LOGIN: Like original version
        await send_update("🔐 Signing in...")
        await page.goto("https://www.linkedin.com", wait_until="domcontentloaded", timeout=10000)
        
        sign_in_btn = await page.query_selector("a.nav__button-secondary")
        if not sign_in_btn:
            # Might already be logged in
            if await self.quick_login_check(page):
                await send_update("✅ Already logged in")
                await session_manager.save_cookies(context, session_id)
                return True
            raise Exception("Could not find sign in button")

        await sign_in_btn.click()
        await page.wait_for_selector("input#username", timeout=8000)
        
        # Faster typing - less delay
        await auth_manager.human_type(page, "input#username", auth_manager.email)
        await asyncio.sleep(0.5)
        await auth_manager.human_type(page, "input#password", auth_manager.password)
        await asyncio.sleep(0.5)
        
        await page.click("button[type='submit']")
        await asyncio.sleep(2)  # Reduced from 3-5 seconds

        # Quick verification
        if await self.quick_login_check(page):
            await send_update("✅ Login successful")
            await session_manager.save_cookies(context, session_id)
            return True
        else:
            raise Exception("Login failed - verification failed")

    async def scrape_job(self, url: str, session_id: str, websocket=None, max_retries: int = 2) -> str:
        """Optimized scraping - matching original speed"""
        async def send_update(message: str):
            if websocket:
                await websocket.send_text(json.dumps({"message": message}))
            print(message)

        p, context = await browser_utils.create_browser_context(session_id)
        page = await context.new_page()

        try:
            for attempt in range(max_retries):
                try:
                    await send_update(f"Attempt {attempt + 1}...")
                    
                    # Use fast login method
                    await self.fast_ensure_logged_in(page, context, session_id, websocket)

                    # Extract job ID
                    job_id = content_extractor.extract_job_id(url)

                    await send_update("🌐 Navigating to job...")
                    await page.goto(url, wait_until="domcontentloaded", timeout=10000)
                    await asyncio.sleep(1)  # Reduced wait

                    # Quick expand check - like original
                    await send_update("🔎 Checking for expand button...")
                    see_more = await page.query_selector("button:has-text('See more')")
                    if see_more:
                        await see_more.click()
                        await asyncio.sleep(0.5)  # Reduced from 2 seconds
                        await send_update("🔽 Expanded job description")

                    # Faster interaction
                    await auth_manager.human_hover(page)
                    await browser_utils.scroll_to_bottom(page)

                    await send_update("📄 Extracting content...")
                    content = await content_extractor.extract_job_content(page)
                    
                    if not content or len(content.strip()) < 50:
                        raise Exception("❌ Failed to extract meaningful content")
                    
                    await send_update(f"✅ Extraction complete. {len(content)} chars")
                    
                    return content

                except Exception as e:
                    await send_update(f"❌ Attempt {attempt + 1} failed: {str(e)}")
                    if "session" in str(e).lower() or "login" in str(e).lower():
                        await session_manager.clear_session_data(session_id)
                    
                    if attempt == max_retries - 1:
                        await send_update("🚫 Max retries reached")
                        raise
                    await asyncio.sleep(5)  # Reduced from 10 seconds
        finally:
            await context.close()
            await p.stop()

        return ""

# Singleton instance
linkedin_scraper = LinkedInScraper()