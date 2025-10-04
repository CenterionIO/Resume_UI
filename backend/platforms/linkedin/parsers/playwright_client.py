import os
import pickle
import logging
from pathlib import Path
from playwright.async_api import async_playwright  # type: ignore
from platforms.linkedin.routers.internal.parser_toggle import run_parser


# -------------------------------------------------
# Setup
# -------------------------------------------------
logger = logging.getLogger(__name__)

# Define base storage directory for cookies
PROJECT_ROOT = Path(__file__).resolve().parents[2]
STORAGE_DIR = PROJECT_ROOT / "storage" / "cookies"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

COOKIE_FILE = STORAGE_DIR / "default_session.pkl"

# -------------------------------------------------
# Browser Context
# -------------------------------------------------
async def get_browser_context():
    """Launch a Playwright browser and manage login cookies."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        if COOKIE_FILE.exists():
            try:
                with open(COOKIE_FILE, "rb") as f:
                    cookies = pickle.load(f)
                await context.add_cookies(cookies)
                logger.info(f"✅ Loaded {len(cookies)} cookies from session file.")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load cookies: {e}")
        else:
            page = await context.new_page()
            logger.info("🌐 Logging into LinkedIn...")
            await page.goto("https://www.linkedin.com/login")
            await page.fill("input#username", os.getenv("LINKEDIN_USER", ""))
            await page.fill("input#password", os.getenv("LINKEDIN_PASSWORD", ""))
            await page.click("button[type=submit]")
            await page.wait_for_timeout(5000)
            cookies = await context.cookies()
            with open(COOKIE_FILE, "wb") as f:
                pickle.dump(cookies, f)
            logger.info(f"💾 Saved {len(cookies)} cookies to session file.")

        return context

# -------------------------------------------------
# Fetch + Parse Job
# -------------------------------------------------
async def fetch_and_parse_job(url: str, parser_override: str = "linkedin_soup"):
    """
    Fetch a LinkedIn job posting and parse using the specified parser.
    Options:
      - linkedin_soup → BeautifulSoup-based parser
      - playwright → DOM-driven parser
      - hybrid → Merged results
    """
    logger.info(f"🚀 Fetching job URL: {url} with parser: {parser_override}")

    context = await get_browser_context()
    page = await context.new_page()
    await page.goto(url)

    parsed_data = await run_parser(page, parser_override=parser_override)

    await context.close()
    return parsed_data
