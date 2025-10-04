# platforms/linkedin/parsers/playwright_client.py
import os
import pickle
import asyncio
from playwright.async_api import async_playwright  # type: ignore
from utils.session_manager import session_manager
from platforms.linkedin.routers.internal.parser_toggle import run_parser
from platforms.linkedin.utils.session_manager import session_manager


async def get_browser_context():
    """Create or restore a persistent LinkedIn session."""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()

    # Load cookies if exist
    cookie_file = session_manager.get_cookie_file("default")
    if cookie_file and cookie_file.exists():
        try:
            cookies = pickle.load(open(cookie_file, "rb"))
            await context.add_cookies(cookies)
        except Exception:
            pass
    else:
        # Manual login once (for local dev)
        page = await context.new_page()
        await page.goto("https://www.linkedin.com/login")
        await page.fill("#username", os.getenv("LINKEDIN_USER", ""))
        await page.fill("#password", os.getenv("LINKEDIN_PASSWORD", ""))
        await page.click("button[type=submit]")
        await page.wait_for_timeout(5000)

        cookies = await context.cookies()

        # Use session manager path
        cookie_file = session_manager.get_cookie_file("default")
        with open(cookie_file, "wb") as f:
            pickle.dump(cookies, f)

    return playwright, browser, context


async def fetch_and_parse_job(url: str, parser_override: str = "linkedin_soup"):
    """Navigate to LinkedIn job and run selected parser."""
    playwright, browser, context = await get_browser_context()
    try:
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded")

        parsed_data = await run_parser(page, parser_override=parser_override)
        return parsed_data

    except Exception as e:
        return {"error": str(e)}

    finally:
        # Ensure graceful teardown
        try:
            await context.close()
        except Exception:
            pass
        try:
            await browser.close()
        except Exception:
            pass
        await playwright.stop()
