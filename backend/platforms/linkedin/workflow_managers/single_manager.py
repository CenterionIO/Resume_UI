"""
Single URL scraping workflow manager.
Orchestrates the complete workflow for scraping a single LinkedIn job posting.

Workflow:
1. Launch browser with proper configuration
2. Validate existing session (check for cookies)
3. Load cookies if valid session exists
4. Check if user is logged in
5. Perform login if needed
6. Fetch HTML using playwright_scraper tool
7. Clean up and return HTML

This manager coordinates session_manager, login, and the scraping tool.
"""
import logging
from playwright.async_api import async_playwright  # type: ignore
from platforms.linkedin.workflow_managers.browser.login.user_credentials import linkedin_login
from platforms.linkedin.workflow_managers.browser.session_management.manager import session_manager
from platforms.linkedin.scrapers.playwright_scraper import fetch_page_html

logger = logging.getLogger(__name__)

# Use a default session ID for single-user scraping
DEFAULT_SESSION_ID = "default_session"


async def scrape_single_job(url: str) -> str:
    """
    Complete workflow for scraping a single LinkedIn job posting.

    This orchestrator handles:
    - Browser lifecycle management
    - Session validation and cookie loading
    - Authentication (login if needed)
    - Delegating actual scraping to playwright_scraper tool
    - Cleanup

    Args:
        url: LinkedIn job posting URL

    Returns:
        str: Raw HTML content of the page

    Raises:
        Exception: If scraping fails (login failure, network error, etc.)
    """
    logger.info(f"🚀 Starting single job scrape workflow for: {url}")

    async with async_playwright() as p:
        # Use Firefox instead of Chromium due to macOS crash issues
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        try:
            # Step 1: Validate and load existing session
            has_valid_session = await session_manager.validate_session(DEFAULT_SESSION_ID)
            if has_valid_session:
                logger.info("🔄 Loading existing session...")
                await session_manager.load_cookies(context, DEFAULT_SESSION_ID)

            page = await context.new_page()

            # Step 2: Navigate to LinkedIn to check authentication
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Step 3: Check if login is required
            if not await linkedin_login.quick_login_check(page):
                logger.info("🔐 Login required - attempting automated login...")

                # If no valid session, perform login
                if not has_valid_session:
                    try:
                        await linkedin_login.perform_login(page, context, DEFAULT_SESSION_ID)
                        logger.info("✅ Login successful, cookies saved")

                        # Navigate back to job URL
                        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    except Exception as e:
                        logger.error(f"❌ Login failed: {e}")
                        raise

            # Step 4: Fetch HTML using the scraper tool
            html = await fetch_page_html(page, url)

            logger.info("✅ Single job scrape workflow complete")
            return html

        except Exception as e:
            logger.error(f"❌ Single job scrape workflow failed: {e}")
            raise
        finally:
            await context.close()
            await browser.close()
