# linkedin_login.py
import os
import re
import json
import asyncio
import random
import pickle
import time
import shutil
from pathlib import Path
from dotenv import load_dotenv # type: ignore
from playwright.async_api import Page, BrowserContext, async_playwright  # type: ignore

# Load environment variables
load_dotenv("/Users/michaelsteele/Documents/python_projects/resume-generator-ui/.env")

# Storage paths (relative to backend directory)
BASE_DIR = Path(__file__).parent
COOKIE_STORAGE_DIR = BASE_DIR / "storage/cookies"
BROWSER_PROFILES_DIR = BASE_DIR / "storage/browser_profiles"

# Ensure directories exist
os.makedirs(COOKIE_STORAGE_DIR, exist_ok=True)
os.makedirs(BROWSER_PROFILES_DIR, exist_ok=True)

# Session configuration
SESSION_MAX_AGE_HOURS = 336  # 2 weeks

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

async def save_cookies(context, session_id):
    """Save cookies for this session - ENHANCED DEBUGGING"""
    print(f"💾 DEBUG: save_cookies called with session_id: {session_id}")
    if session_id:
        cookies = await context.cookies()
        cookie_file = get_cookie_file(session_id)
        
        print(f"💾 DEBUG: Saving {len(cookies)} cookies to: {cookie_file}")
        for cookie in cookies:
            print(f"  💾 {cookie.get('name')} - {cookie.get('domain')}")
        
        with open(str(cookie_file), 'wb') as f:
            pickle.dump(cookies, f)
        
        print(f"✅ Cookies saved. File exists: {os.path.exists(cookie_file)}")
    else:
        print("❌ No session_id provided to save_cookies")

async def load_cookies(context, session_id):
    """Load cookies for this session - ENHANCED DEBUGGING"""
    print(f"🔄 DEBUG: load_cookies called with session_id: {session_id}")
    if session_id:
        cookie_file = get_cookie_file(session_id)
        print(f"🔄 DEBUG: Cookie file path: {cookie_file}")
        print(f"🔄 DEBUG: Cookie file exists: {os.path.exists(cookie_file)}")
        
        if cookie_file is not None and os.path.exists(cookie_file):
            print(f"🔄 DEBUG: Loading cookies from: {cookie_file}")
            with open(cookie_file, 'rb') as f:
                cookies = pickle.load(f)
            
            print(f"🔄 DEBUG: Loaded {len(cookies)} cookies")
            linkedin_cookies = [c for c in cookies if 'linkedin' in c.get('domain', '')]
            print(f"🔄 DEBUG: {len(linkedin_cookies)} LinkedIn cookies found")
            
            for cookie in linkedin_cookies[:3]:  # Show first 3 LinkedIn cookies
                print(f"  🍪 {cookie.get('name')} - {cookie.get('domain')}")
            
            await context.add_cookies(cookies)
            print("✅ Cookies loaded successfully")
            return True
        else:
            print("❌ No cookie file found or session_id missing")
    return False

async def validate_session(session_id):
    """Check if a session has valid cookies"""
    if not session_id:
        return False
    
    cookie_file = get_cookie_file(session_id)
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

async def clear_session_data(session_id):
    """Clear all data for a session"""
    try:
        # Remove cookie file
        cookie_file = get_cookie_file(session_id)
        if cookie_file and os.path.exists(cookie_file):
            os.remove(cookie_file)
            print(f"🗑️ Removed cookie file: {cookie_file}")
        
        # Remove browser profile
        profile_dir = get_browser_profile_dir(session_id)
        if profile_dir and os.path.exists(profile_dir):
            shutil.rmtree(profile_dir)
            print(f"🗑️ Removed browser profile: {profile_dir}")
            
    except Exception as e:
        print(f"❌ Error clearing session data: {e}")

async def cleanup_old_sessions():
    """Remove sessions older than SESSION_MAX_AGE_HOURS"""
    current_time = time.time()
    max_age_seconds = SESSION_MAX_AGE_HOURS * 3600
    
    print("🧹 Checking for old sessions to cleanup...")
    
    # Cleanup old cookie files
    for cookie_file in COOKIE_STORAGE_DIR.glob("*.pkl"):
        if (current_time - cookie_file.stat().st_mtime) > max_age_seconds:
            session_id = cookie_file.stem
            print(f"🧹 Removing expired session: {session_id}")
            await clear_session_data(session_id)
    
    # Cleanup old browser profiles
    for profile_dir in BROWSER_PROFILES_DIR.iterdir():
        if profile_dir.is_dir() and (current_time - profile_dir.stat().st_mtime) > max_age_seconds:
            print(f"🧹 Removing expired browser profile: {profile_dir.name}")
            shutil.rmtree(profile_dir)

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

async def wait_for_random_delay(min_seconds=1, max_seconds=3):
    """Wait for a random delay to simulate human behavior"""
    await asyncio.sleep(random.uniform(min_seconds, max_seconds))

async def wait_for_linkedin_load(page, timeout=30000):
    """Wait for LinkedIn to load sufficiently without strict networkidle"""
    try:
        # Wait for main content to appear
        await page.wait_for_selector(".scaffold-layout__main, .jobs-description__content, .feed-identity-module", 
                                   timeout=timeout)
        print("✅ LinkedIn main content loaded")
    except Exception as e:
        print(f"⚠️ Content loading slow, but continuing: {e}")
    
    # Wait a bit more for any additional loading
    await wait_for_random_delay(2, 3)

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

async def ensure_logged_in(page, context, session_id, websocket=None):
    """Ensure we're logged in, using cookies if available"""
    async def send_update(message):
        if websocket:
            await websocket.send_text(json.dumps({"message": message}))
        print(message)

    # Try to load existing cookies first
    cookies_loaded = await load_cookies(context, session_id)
    
    if cookies_loaded:
        await send_update("🔄 Checking existing session...")
        await page.goto("https://www.linkedin.com/feed", wait_until="domcontentloaded", timeout=15000)
        await wait_for_linkedin_load(page)
        
        if await is_logged_in(page):
            await send_update("✅ Using existing authenticated session")
            return True
        else:
            await send_update("❌ Session expired, logging in fresh...")
            await clear_session_data(session_id)
    
    # Fresh login required
    await send_update("🔐 Starting fresh login...")
    await page.goto("https://www.linkedin.com", wait_until="domcontentloaded", timeout=15000)
    await wait_for_linkedin_load(page)
    
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
    
    await human_hover(page)
    await sign_in_btn.click()
    await page.wait_for_selector("input#username", timeout=10000)
    
    # Enter credentials
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    
    await send_update("Entering credentials...")
    await human_type(page, "input#username", email)
    await wait_for_random_delay(1, 2)
    await human_type(page, "input#password", password)
    await wait_for_random_delay(1, 2)
    
    await handle_remember_device(page)
    
    await send_update("Submitting login...")
    await page.click("button[type='submit']")
    await wait_for_random_delay(3, 5)

    # Verify login success
    if await is_logged_in(page):
        await send_update("✅ Login successful")
        await save_cookies(context, session_id)
        return True
    else:
        raise Exception("Login failed - could not verify login status")

async def patch_webdriver(p, session_id=None):
    """Create browser context with session persistence"""
    print(f"🔧 DEBUG: patch_webdriver called with session_id: {session_id}")
    
    # Run cleanup on startup (optional - can be moved to separate maintenance task)
    await cleanup_old_sessions()
    
    if session_id:
        # Use persistent profile for this session
        profile_dir = get_browser_profile_dir(session_id)
        print(f"🔧 DEBUG: Creating persistent context with profile: {profile_dir}")
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=['--no-sandbox', '--disable-setuid-sandbox'],
            timeout=60000  # Increased timeout for operations
        )
        print(f"🔧 DEBUG: Persistent context created for session: {session_id}")
    else:
        print("🔧 DEBUG: Creating temporary browser context (no session_id)")
        # Temporary session
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            timeout=60000  # Increased timeout
        )
    
    return context

async def login_and_scrape(url: str, websocket=None, session_id=None, max_retries: int = 3) -> str:
    # CRITICAL DEBUG LOGGING
    print(f"🔧 DEBUG: ========== STARTING SCRAPE ==========")
    print(f"🔧 DEBUG: Session ID received: {session_id}")
    print(f"🔧 DEBUG: URL: {url}")
    
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
                await send_update(f"Attempt {attempt + 1}: Setting up session...")
                
                # Use the new ensure_logged_in function
                await ensure_logged_in(page, context, session_id, websocket)

                # Extract job ID from URL
                job_id_match = re.search(r'/jobs/view/(\d+)', url)
                if not job_id_match:
                    raise Exception("❌ Invalid LinkedIn job URL")

                await send_update(f"🌐 Navigating to job posting...")
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await wait_for_linkedin_load(page)

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
                
                print(f"🔧 DEBUG: ========== SCRAPE COMPLETED SUCCESSFULLY ==========")
                return content

            except Exception as e:
                await send_update(f"❌ Attempt {attempt + 1} failed: {str(e)}")
                print(f"🔧 DEBUG: Attempt {attempt + 1} failed with error: {e}")
                if "session expired" in str(e).lower() or "login" in str(e).lower():
                    await send_update("🔄 Session issue detected, clearing data...")
                    await clear_session_data(session_id)
                
                if attempt == max_retries - 1:
                    await send_update("🚫 Max retries reached. Scraping failed.")
                    raise
                await send_update(f"🔄 Retrying in 10 seconds...")
                await asyncio.sleep(10)

        return ""