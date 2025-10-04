# modules/scraping/platforms/linkedin.py
import asyncio
import json
from playwright.async_api import Page # type: ignore
from utils.linkedin_login import linkedin_login
from utils.session_manager import session_manager
from utils.browser_utils import browser_utils
from modules.linkedin_html_parser import extract_summary_section

class LinkedInScraper:
    def __init__(self):
        self.platform_name = "linkedin"

    async def ensure_logged_in(self, page: Page, context, session_id: str, websocket=None) -> bool:
        """Ensure user is logged in - PROPER session reuse"""
        async def send_update(msg):
            if websocket:
                await websocket.send_text(json.dumps({"message": msg}))
            print(msg)

        # Step 1: Check if we have a valid existing session
        has_valid_session = await session_manager.validate_session(session_id)
        
        if has_valid_session:
            await send_update("🔄 Loading existing session...")
            cookies_loaded = await session_manager.load_cookies(context, session_id)
            
            if cookies_loaded:
                await send_update("🔗 Testing session validity...")
                await page.goto("https://www.linkedin.com/feed", wait_until="domcontentloaded", timeout=10000)
                
                if await linkedin_login.quick_login_check(page):
                    await send_update("✅ Using existing authenticated session")
                    return True
                else:
                    await send_update("❌ Session expired, will re-authenticate")
                    await session_manager.clear_session_data(session_id)
        
        # Step 2: Perform fresh login
        await send_update("🔐 Starting authentication...")
        login_success = await linkedin_login.perform_login(page, context, session_id, websocket)
        
        if login_success:
            await send_update("💾 Saving session for future use...")
            await session_manager.save_cookies(context, session_id)
            return True
        
        return False

    async def scrape_job(self, url: str, session_id: str, websocket=None, max_retries: int = 2) -> dict:
        """Scrape job with proper session persistence"""
        async def send_update(msg: str):
            if websocket:
                await websocket.send_text(json.dumps({"message": msg}))
            print(msg)

        # Use browser_utils with session persistence
        p, context = await browser_utils.create_browser_context(session_id)
        page = await context.new_page()

        try:
            for attempt in range(max_retries):
                try:
                    await send_update(f"🔄 Attempt {attempt + 1} (Session: {session_id})...")

                    # Ensure logged in with proper session handling
                    await self.ensure_logged_in(page, context, session_id, websocket)

                    # Navigate to job
                    await send_update("🌐 Navigating to job...")
                    await page.goto(url, wait_until="domcontentloaded", timeout=15000)

                    # Wait for content
                    await send_update("⏳ Waiting for job content...")
                    try:
                        await page.wait_for_selector(
                            "div.top-card-layout__entity-info, div.top-card-layout__card, div.jobs-unified-top-card",
                            timeout=10000
                        )
                    except:
                        await send_update("⚠️ Top card not found, continuing anyway")

                    # Extract and parse
                    await send_update("📄 Extracting page HTML...")
                    full_page_html = await page.content()

                    if not full_page_html or len(full_page_html.strip()) < 500:
                        raise Exception("❌ Failed to extract meaningful HTML")

                    await send_update("🔄 Parsing job content...")
                    parsed_result = await extract_summary_section(full_page_html, websocket)

                    if not parsed_result or not parsed_result.get("parsed_text"):
                        raise Exception("❌ HTML parsing failed")

                    await send_update(f"✅ Parsing complete - {len(parsed_result.get('sections', []))} sections")

                    return {
                        "type": "complete",
                        "job_data": parsed_result["parsed_text"],
                        "message": parsed_result["message"],
                        "metadata": parsed_result.get("metadata", {}),
                        "sections": parsed_result.get("sections", []),
                        "session_id": session_id  # Important: return session_id for reuse
                    }

                except Exception as e:
                    await send_update(f"❌ Attempt {attempt + 1} failed: {str(e)}")
                    if "session" in str(e).lower() or "login" in str(e).lower():
                        await session_manager.clear_session_data(session_id)

                    if attempt == max_retries - 1:
                        await send_update("🚫 Max retries reached")
                        raise
                    await asyncio.sleep(5)
        finally:
            await context.close()
            await p.stop()

        return {"type": "error", "error": "Scraping failed after all retries"}

linkedin_scraper = LinkedInScraper()