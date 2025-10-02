# linkedin_login.py
import os
import re
import json
import asyncio
import random
import pickle
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# Load environment variables
load_dotenv("/Users/michaelsteele/Documents/python_projects/resume-generator-ui/.env")

# Storage paths (relative to backend directory)
BASE_DIR = Path(__file__).parent
COOKIE_STORAGE_DIR = BASE_DIR / "storage/cookies"
BROWSER_PROFILES_DIR = BASE_DIR / "storage/browser_profiles"
SCREENSHOTS_DIR = BASE_DIR / "storage/screenshots"

# Ensure directories exist
os.makedirs(COOKIE_STORAGE_DIR, exist_ok=True)
os.makedirs(BROWSER_PROFILES_DIR, exist_ok=True)
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def get_browser_profile_dir(session_id):
    """Get browser profile directory for this session"""
    if session_id:
        profile_dir = BROWSER_PROFILES_DIR / session_id
        os.makedirs(profile_dir, exist_ok=True)
        print(f"🔧 DEBUG: Browser profile directory: {profile_dir}")
        return str(profile_dir)
    return None

def get_cookie_file(session_id):
    """Get cookie file path for this session"""
    if session_id:
        cookie_file = COOKIE_STORAGE_DIR / f"{session_id}.pkl"
        print(f"🔧 DEBUG: Cookie file path: {cookie_file}")
        return cookie_file
    return None

def get_screenshot_path(job_id):
    """Get screenshot path"""
    return SCREENSHOTS_DIR / f"{job_id}.png"

async def save_cookies(context, session_id):
    """Save cookies for this session"""
    print(f"🔧 DEBUG: save_cookies called with session_id: {session_id}")
    if session_id:
        cookies = await context.cookies()
        cookie_file = get_cookie_file(session_id)
        if cookie_file is not None:
            print(f"🔧 DEBUG: Saving {len(cookies)} cookies to: {cookie_file}")
            with open(str(cookie_file), 'wb') as f:
                pickle.dump(cookies, f)
            print(f"✅ Cookies saved to: {cookie_file}")
            
            # Verify the file was created
            if os.path.exists(cookie_file):
                print(f"✅ Cookie file verified: {cookie_file} exists")
            else:
                print(f"❌ Cookie file NOT created: {cookie_file}")
        else:
            print("❌ No cookie file path generated")
    else:
        print("❌ No session_id provided to save_cookies")

async def load_cookies(context, session_id):
    """Load cookies for this session"""
    print(f"🔧 DEBUG: load_cookies called with session_id: {session_id}")
    if session_id:
        cookie_file = get_cookie_file(session_id)
        if cookie_file is not None and os.path.exists(cookie_file):
            print(f"🔧 DEBUG: Loading cookies from: {cookie_file}")
            with open(cookie_file, 'rb') as f:
                cookies = pickle.load(f)
            await context.add_cookies(cookies)
            print(f"✅ Cookies loaded from: {cookie_file} - {len(cookies)} cookies")
            return True
        else:
            print(f"❌ Cookie file not found: {cookie_file}")
    else:
        print("❌ No session_id provided to load_cookies")
    return False

async def human_type(page, selector, text):
    """Simulate human typing with random delays"""
    await page.click(selector, delay=100)
    await asyncio.sleep(0.5)
    
    for char in text:
        await page.type(selector, char, delay=random.uniform(50, 150))
        if random.random() > 0.9:
            await asyncio.sleep(random.uniform(0.1, 0.3))

async def human_hover(page):
    """Simulate human mouse movements"""
    for _ in range(3):
        x = random.randint(100, 500)
        y = random.randint(100, 500)
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.1, 0.5))

async def scroll_to_bottom(page):
    """Scroll like a human with variable speed"""
    viewport_height = await page.evaluate("window.innerHeight")
    scroll_height = await page.evaluate("document.body.scrollHeight")
    
    current_position = 0
    while current_position < scroll_height:
        scroll_amount = random.randint(100, 300)
        current_position += scroll_amount
        await page.evaluate(f"window.scrollTo(0, {current_position})")
        await asyncio.sleep(random.uniform(0.1, 0.5))

async def handle_remember_device(page):
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

async def extract_all_content(page):
    """Extract job description content"""
    try:
        job_description = await page.query_selector(".jobs-description__content")
        if job_description:
            content = await job_description.text_content()
            if content and len(content.strip()) > 100:
                return content.strip()
        
        body_text = await page.text_content("body")
        return body_text[:3000]
        
    except Exception as e:
        print(f"Error extracting content: {e}")
        return f"Error extracting job description: {str(e)}"

async def save_screenshot(page, job_id):
    """Save screenshot of the page"""
    path = get_screenshot_path(job_id)
    await page.screenshot(path=path, full_page=True)
    print(f"🔧 DEBUG: Screenshot saved to: {path}")
    return str(path)

async def patch_webdriver(p, session_id=None):
    """Create browser context with session persistence"""
    print(f"🔧 DEBUG: patch_webdriver called with session_id: {session_id}")
    
    if session_id:
        # Use persistent profile for this session
        profile_dir = get_browser_profile_dir(session_id)
        print(f"🔧 DEBUG: Creating persistent context with profile: {profile_dir}")
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        # Load any existing cookies
        print(f"🔧 DEBUG: Attempting to load cookies for session: {session_id}")
        await load_cookies(context, session_id)
    else:
        print("🔧 DEBUG: Creating temporary browser context (no session_id)")
        # Temporary session
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    
    return context

async def wait_for_random_delay(min_seconds=1, max_seconds=3):
    """Wait for a random delay to simulate human behavior"""
    await asyncio.sleep(random.uniform(min_seconds, max_seconds))

async def is_logged_in(page):
    """Check if we're already logged in"""
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

async def login_and_scrape(url: str, websocket=None, session_id=None, max_retries: int = 3) -> str:
    # CRITICAL DEBUG LOGGING
    print(f"🔧 DEBUG: ========== STARTING SCRAPE ==========")
    print(f"🔧 DEBUG: Session ID received: {session_id}")
    print(f"🔧 DEBUG: URL: {url}")
    print(f"🔧 DEBUG: Storage directories:")
    print(f"🔧 DEBUG - Cookies: {COOKIE_STORAGE_DIR} (exists: {os.path.exists(COOKIE_STORAGE_DIR)})")
    print(f"🔧 DEBUG - Browser profiles: {BROWSER_PROFILES_DIR} (exists: {os.path.exists(BROWSER_PROFILES_DIR)})")
    print(f"🔧 DEBUG - Screenshots: {SCREENSHOTS_DIR} (exists: {os.path.exists(SCREENSHOTS_DIR)})")
    
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    
    if not email or not password:
        raise ValueError("Missing LinkedIn credentials.")

    async def send_update(message: str):
        if websocket:
            await websocket.send_text(json.dumps({"message": message}))
        print(message)

    async with async_playwright() as p:
        print(f"🔧 DEBUG: Creating browser context with session_id: {session_id}")
        context = await patch_webdriver(p, session_id)
        page = await context.new_page()

        for attempt in range(max_retries):
            try:
                await send_update(f"Attempt {attempt + 1}: Checking login status...")
                
                await page.goto("https://www.linkedin.com", wait_until="networkidle")
                await wait_for_random_delay(2, 4)
                
                login_status = await is_logged_in(page)
                print(f"🔧 DEBUG: Login status check result: {login_status}")
                
                if login_status:
                    await send_update("🔓 Already logged in with existing session")
                    print("🔧 DEBUG: User is already logged in - cookies should have been loaded")
                else:
                    await send_update("🔐 No active session — signing in...")
                    print("🔧 DEBUG: No active session - performing fresh login")
                    
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
                            print(f"🔧 DEBUG: Found sign in button with selector: {selector}")
                            break

                    if not sign_in_btn:
                        raise Exception("Could not find sign in button")
                    
                    await human_hover(page)
                    await sign_in_btn.click()
                    await page.wait_for_selector("input#username", timeout=10000)
                    
                    await send_update("Entering credentials...")
                    await human_type(page, "input#username", email)
                    await wait_for_random_delay(1, 2)
                    await human_type(page, "input#password", password)
                    await wait_for_random_delay(1, 2)
                    
                    await handle_remember_device(page)
                    
                    await send_update("Submitting login...")
                    await page.click("button[type='submit']")
                    await wait_for_random_delay(3, 5)

                    login_success = await is_logged_in(page)
                    print(f"🔧 DEBUG: Post-login status check: {login_success}")
                    
                    if login_success:
                        await send_update("✅ Login successful")
                        # Save cookies for next time
                        print(f"🔧 DEBUG: About to save cookies with session_id: {session_id}")
                        await save_cookies(context, session_id)
                    else:
                        raise Exception("Login failed")

                # Extract job ID from URL
                job_id_match = re.search(r'/jobs/view/(\d+)', url)
                if not job_id_match:
                    raise Exception("❌ Invalid LinkedIn job URL")
                job_id = job_id_match.group(1)
                print(f"🔧 DEBUG: Extracted job ID: {job_id}")

                await send_update(f"🌐 Navigating to job posting: {job_id}")
                await page.goto(url, wait_until="networkidle")
                await wait_for_random_delay(3, 5)

                # Try to expand job description
                await send_update("🔎 Looking for expandable job description...")
                expand_selectors = [
                    "button:has-text('See more')",
                    "button:has-text('See more')",
                    "button[aria-label*='see more']",
                    ".jobs-description-expand"
                ]
                
                for selector in expand_selectors:
                    see_more = await page.query_selector(selector)
                    if see_more:
                        await send_update("🔽 Expanding job description...")
                        await human_hover(page)
                        await see_more.click()
                        await wait_for_random_delay(1, 2)
                        break
                else:
                    await send_update("ℹ️ No expand button found")

                await send_update("🖱️ Simulating human interaction...")
                await human_hover(page)
                await scroll_to_bottom(page)

                await send_update("📄 Extracting job description...")
                content = await extract_all_content(page)
                
                if not content or len(content.strip()) < 50:
                    raise Exception("❌ Failed to extract meaningful content")
                
                await send_update(f"✅ Extraction complete. Captured {len(content)} characters.")
                
                # Save screenshot
                screenshot_path = await save_screenshot(page, job_id)
                await send_update(f"📸 Screenshot saved to: {screenshot_path}")

                print(f"🔧 DEBUG: ========== SCRAPE COMPLETED SUCCESSFULLY ==========")
                return content

            except Exception as e:
                await send_update(f"❌ Attempt {attempt + 1} failed: {str(e)}")
                print(f"🔧 DEBUG: Attempt {attempt + 1} failed with error: {e}")
                if attempt == max_retries - 1:
                    await send_update("🚫 Max retries reached. Scraping failed.")
                    raise
                await send_update(f"🔄 Retrying in 10 seconds...")
                await asyncio.sleep(10)

        return ""