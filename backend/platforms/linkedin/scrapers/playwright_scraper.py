"""
Pure Playwright scraper tool for fetching LinkedIn job HTML.
This module contains ONLY the scraping logic - no session management or authentication.
"""
import logging
from playwright.async_api import Page  # type: ignore

logger = logging.getLogger(__name__)


async def fetch_page_html(page: Page, url: str) -> str:
    """
    Fetch HTML content from a LinkedIn job URL using an existing Playwright page.

    This is a pure scraping tool - it assumes the page is already authenticated
    and ready to navigate. Session management and login should be handled by
    the workflow manager before calling this function.

    Args:
        page: Authenticated Playwright page object
        url: LinkedIn job posting URL

    Returns:
        str: Raw HTML content of the page
    """
    logger.info(f"🌐 Fetching URL: {url}")

    try:
        # Navigate to job posting
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        logger.info("✅ Page loaded")

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
