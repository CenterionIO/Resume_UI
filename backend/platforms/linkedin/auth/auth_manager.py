# modules/auth/auth_manager.py
import asyncio
import random
import json
from playwright.async_api import Page # type: ignore
from core.config import LINKEDIN_EMAIL, LINKEDIN_PASSWORD

class AuthManager:
    def __init__(self):
        if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
            raise ValueError("Missing LinkedIn credentials in environment variables.")
        self.email = LINKEDIN_EMAIL
        self.password = LINKEDIN_PASSWORD

    async def human_type(self, page: Page, selector: str, text: str):
        """Simulate human typing with random delays"""
        await page.click(selector, delay=100)
        await asyncio.sleep(0.5)
        
        for char in text:
            await page.type(selector, char, delay=random.uniform(50, 150))
            if random.random() > 0.9:
                await asyncio.sleep(random.uniform(0.1, 0.3))

    async def human_hover(self, page: Page):
        """Simulate human mouse movements"""
        for _ in range(3):
            x = random.randint(100, 500)
            y = random.randint(100, 500)
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.5))

    async def handle_remember_device(self, page: Page):
        """Handle 'Remember this device' prompt if it appears"""
        try:
            remember_selectors = [
                "input[name='rememberMe']",
                "input[type='checkbox']",
                ".remember-me",
                "label:has-text('Remember this device')"
            ]
            
            for selector in remember_selectors:
                remember_checkbox = await page.query_selector(selector)
                if remember_checkbox:
                    is_checked = await remember_checkbox.is_checked()
                    if not is_checked:
                        await remember_checkbox.check()
                        print("✅ Checked 'Remember this device'")
                    break
        except Exception as e:
            print(f"Note: Could not handle remember device: {e}")

    async def is_logged_in(self, page: Page) -> bool:
        """Check if we're already logged in to LinkedIn"""
        try:
            logged_in_indicators = [
                ".global-nav__me",
                ".nav-item__profile",
                "[data-test-global-nav-link='Me']",
                ".feed-identity-module"
            ]
            
            for selector in logged_in_indicators:
                element = await page.query_selector(selector)
                if element:
                    print(f"🔧 DEBUG: Logged in - found indicator: {selector}")
                    return True
                    
            if "feed" in page.url or "linkedin.com/feed" in page.url:
                print("🔧 DEBUG: Logged in - on feed page")
                return True
            
            print("🔧 DEBUG: Not logged in - no indicators found")
            return False
            
        except Exception as e:
            print(f"Error checking login status: {e}")
            return False

    async def perform_fresh_login(self, page: Page, websocket=None) -> bool:
        """Perform a fresh LinkedIn login"""
        async def send_update(message: str):
            if websocket:
                await websocket.send_text(json.dumps({"message": message}))
            print(message)

        await send_update("🔐 Starting fresh login...")
        await page.goto("https://www.linkedin.com", wait_until="domcontentloaded", timeout=15000)
        
        # Find and click sign in button
        sign_in_selectors = [
            "a.nav__button-secondary",
            "a[data-tracking-control_name='guest_homepage-basic_nav-header-signin']",
            "a[href*='login']",
            "button:has-text('Sign in')"
        ]
        
        sign_in_btn = None
        for selector in sign_in_selectors:
            sign_in_btn = await page.query_selector(selector)
            if sign_in_btn:
                break

        if not sign_in_btn:
            raise Exception("Could not find sign in button")
        
        await self.human_hover(page)
        await sign_in_btn.click()
        await page.wait_for_selector("input#username", timeout=10000)
        
        await send_update("Entering credentials...")
        await self.human_type(page, "input#username", self.email)
        await asyncio.sleep(random.uniform(1, 2))
        await self.human_type(page, "input#password", self.password)
        await asyncio.sleep(random.uniform(1, 2))
        
        await self.handle_remember_device(page)
        
        await send_update("Submitting login...")
        await page.click("button[type='submit']")
        await asyncio.sleep(random.uniform(3, 5))

        # Verify login success
        login_success = await self.is_logged_in(page)
        if login_success:
            await send_update("✅ Login successful")
            return True
        else:
            raise Exception("Login failed - could not verify login status")

# Singleton instance
auth_manager = AuthManager()