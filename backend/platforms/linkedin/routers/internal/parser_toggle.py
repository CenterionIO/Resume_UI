# backend/platforms/linkedin/routers/internal/parser_toggle.py
import os
import json
import logging
from typing import Dict, Optional
from playwright.async_api import Page  # type: ignore
from platforms.linkedin.parsers.linkedin_soup_parser import LinkedInParser
from platforms.linkedin.parsers.job_parser import parse_job_posting 

logger = logging.getLogger(__name__)


# --------------------------------------------------
# HTML-Only Parsing (Soup)
# --------------------------------------------------
async def parse_linkedin_html(html_content: str, websocket=None) -> Dict:
    """
    Parse LinkedIn HTML using the LinkedInParser.
    Can be triggered directly (non-Playwright workflows).
    """
    if websocket:
        await websocket.send_text(json.dumps({"message": "⚙️ Using LinkedInParser"}))

    parser = LinkedInParser()
    parsed_data = parser.parse_linkedin_job(html_content)


    return {
        "parsed_text": json.dumps(parsed_data, indent=2),
        "message": "Parsed successfully using LinkedInParser",
        "metadata": parsed_data,
        "sections": list(parsed_data.keys()),
    }


# --------------------------------------------------
# Unified Parser Entrypoint
# --------------------------------------------------
async def run_parser(page: Page, parser_override: Optional[str] = None) -> Dict:
    """
    Unified entrypoint for parsing LinkedIn job pages.
    Supports toggling between parser modes:
      - parser_override="linkedin_soup" → BeautifulSoup parser
      - parser_override="playwright"    → Playwright DOM parser
      - parser_override="hybrid"        → Combine both
    """
    html = await page.content()
    logger.info(f"Parsing LinkedIn HTML content (length: {len(html)})")

    try:
        # --- Playwright only ---
        if parser_override == "playwright":
            logger.info("Using Playwright parser")
            return await parse_job_posting(page)

        # --- BeautifulSoup only ---
        elif parser_override == "linkedin_soup":
            logger.info("Using LinkedInParser")
            parser = LinkedInParser()
            return parser.parse_linkedin_job(html)


        # --- Hybrid: merge results ---
        elif parser_override == "hybrid":
            logger.info("Using hybrid parser (Soup + Playwright)")
            parser = LinkedInParser()
            soup_data = parser.parse_linkedin_job(html)

            playwright_data = await parse_job_posting(page)

            # Merge, prioritizing Playwright data where non-empty
            merged = {**soup_data, **{k: v for k, v in playwright_data.items() if v}}
            return merged

        # --- Default fallback ---
        else:
            logger.info("Using default parser (Soup → Playwright fallback)")
            try:
                parser = LinkedInParser()
                result = parser.parse_linkedin_job(html)

                if result.get("title") and result.get("company"):
                    return result
            except Exception as e:
                logger.warning(f"Soup parser failed: {e}")

            try:
                return await parse_job_posting(page)
            except Exception as e:
                logger.error(f"Playwright parser failed: {e}")
                raise e

    except Exception as e:
        logger.error(f"Parser failed: {e}")
        return {
            "company": None,
            "title": None,
            "location": None,
            "posted_time": None,
            "applicants": None,
            "salary": None,
            "work_arrangement": [],
            "employment_type": [],
            "description": None,
            "sections": {},
            "error": str(e),
        }
