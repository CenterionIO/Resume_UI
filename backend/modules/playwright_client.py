# modules/playwright_client.py
from playwright.async_api import async_playwright # type: ignore
from utils.session_manager import session_manager
from modules.job_parser import parse_job_posting

async def fetch_and_parse_job(url: str, session_id: str = "default"):
    """Fetch LinkedIn job posting and parse it."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Create a context tied to this session
        profile_dir = session_manager.get_browser_profile_dir(session_id)
        context = await browser.new_context(storage_state=None, user_data_dir=profile_dir)

        # Load cookies if they exist
        await session_manager.load_cookies(context, session_id)

        page = await context.new_page()
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state("networkidle")

        # Parse job posting using Playwright selectors
        parsed = await parse_job_posting(page)

        # Save cookies back to storage
        await session_manager.save_cookies(context, session_id)

        await context.close()
        await browser.close()

        return parsed
