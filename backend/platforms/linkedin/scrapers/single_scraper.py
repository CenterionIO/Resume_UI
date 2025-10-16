"""
Simple URL scraper using Playwright to fetch LinkedIn job HTML.
"""
import logging
from playwright.async_api import async_playwright  # type: ignore
from platforms.linkedin.workflow_managers.browser.login.user_credentials import linkedin_login
from platforms.linkedin.workflow_managers.browser.session_management.manager import session_manager

logger = logging.getLogger(__name__)

# Use a default session ID for single-user scraping
DEFAULT_SESSION_ID = "default_session"


async def fetch_job_html(url: str) -> str:
    """
    Fetch HTML content from a LinkedIn job URL using Playwright.
    Handles LinkedIn authentication with cookie persistence.

    Args:
        url: LinkedIn job posting URL

    Returns:
        str: Raw HTML content of the page
    """
    logger.info(f"🌐 Fetching URL: {url}")

    async with async_playwright() as p:
        # Use Firefox instead of Chromium due to macOS crash issues
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Load existing session cookies if available
        has_valid_session = await session_manager.validate_session(DEFAULT_SESSION_ID)
        if has_valid_session:
            logger.info("🔄 Loading existing session...")
            await session_manager.load_cookies(context, DEFAULT_SESSION_ID)

        page = await context.new_page()

        try:
            # Navigate to job posting
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            logger.info("✅ Page loaded")

            # Check if login is required
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

            # Wait for job content
            try:
                await page.wait_for_selector(
                    "div.top-card-layout__entity-info, div.jobs-unified-top-card, div.show-more-less-html",
                    timeout=10000
                )
            except Exception as e:
                logger.warning(f"⚠️ Timeout waiting for job content: {e}")

            # Click "Show more" buttons if present
            try:
                see_more_buttons = page.locator("button[aria-label*='more'], button:has-text('Show more')")
                count = await see_more_buttons.count()
                for i in range(min(count, 3)):
                    await see_more_buttons.nth(i).click()
                    await page.wait_for_timeout(300)
                logger.info(f"✅ Expanded {min(count, 3)} sections")
            except Exception:
                pass

            # Get HTML content
            html = await page.content()
            logger.info(f"✅ Retrieved HTML ({len(html)} chars)")

            return html

        except Exception as e:
            logger.error(f"❌ Error fetching URL: {e}")
            raise
        finally:
            await context.close()
            await browser.close()
