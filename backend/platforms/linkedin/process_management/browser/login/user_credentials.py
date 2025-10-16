# utils/linkedin_login.py
import os
import json
import asyncio
import random
from playwright.async_api import Page, BrowserContext # type: ignore
from platforms.linkedin.process_management.browser.session_management.manager import session_manager

class LinkedInLogin:
    def __init__(self):
        # For testing - single user credentials from environment
        self.test_email = os.getenv("LINKEDIN_EMAIL")
        self.test_password = os.getenv("LINKEDIN_PASSWORD")
        
        if not self.test_email or not self.test_password:
            raise ValueError("❌ LinkedIn credentials not found in environment")

    async def human_type(self, page, selector, text):
        """Simulate human typing"""
        await page.click(selector, delay=100)
        await asyncio.sleep(0.5)
        
        for char in text:
            await page.type(selector, char, delay=random.uniform(50, 150))
            if random.random() > 0.9:
                await asyncio.sleep(random.uniform(0.1, 0.3))

    async def quick_login_check(self, page: Page) -> bool:
        """Quick check if user is logged in"""
        try:
            if "feed" in page.url or "linkedin.com/feed" in page.url:
                return True
            logged_in = await page.query_selector(
                ".global-nav__me, .nav-item__profile, [data-test-global-nav-link='Me']"
            )
            return logged_in is not None
        except:
            return False

    async def perform_login(self, page: Page, context: BrowserContext, session_id: str, websocket=None) -> bool:
        """Perform the actual LinkedIn login"""
        async def send_update(msg):
            if websocket:
                await websocket.send_text(json.dumps({"message": msg}))
            print(msg)

        await send_update("🔐 Starting LinkedIn login...")
        await page.goto("https://www.linkedin.com", wait_until="domcontentloaded", timeout=15000)

        # Find and click sign in button
        sign_in_btn = await page.query_selector("a.nav__button-secondary")
        if not sign_in_btn:
            if await self.quick_login_check(page):
                await send_update("✅ Already logged in")
                await session_manager.save_cookies(context, session_id)
                return True
            raise Exception("Could not find sign-in button")

        await sign_in_btn.click()
        await page.wait_for_selector("input#username", timeout=8000)

        # Enter credentials (using test credentials for now)
        await send_update("📝 Entering credentials...")
        await self.human_type(page, "input#username", self.test_email)
        await asyncio.sleep(0.5)
        await self.human_type(page, "input#password", self.test_password)
        await asyncio.sleep(0.5)
        
        await send_update("🚀 Submitting login...")
        await page.click("button[type='submit']")
        await asyncio.sleep(2)

        # Verify login success
        if await self.quick_login_check(page):
            await send_update("✅ Login successful")
            await session_manager.save_cookies(context, session_id)
            return True
        else:
            raise Exception("Login failed")

# Singleton
linkedin_login = LinkedInLogin()