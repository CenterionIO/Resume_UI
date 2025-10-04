# modules/parser_router.py
from typing import Dict, Optional
from playwright.async_api import Page
from modules.job_parser import parse_job_posting
from modules.linkedin_soup_parser import LinkedInSoupParser


async def run_parser(page: Page, parser_override: Optional[str] = None) -> Dict:
    """
    Unified parser entrypoint.
    - parser_override="playwright" -> use Playwright selectors
    - parser_override="linkedin_soup" -> use BeautifulSoup fallback
    - parser_override="hybrid" -> run both and merge
    """
    html = await page.content()

    if parser_override == "playwright":
        return await parse_job_posting(page)

    elif parser_override == "linkedin_soup":
        parser = LinkedInSoupParser()
        return parser.parse(html)

    elif parser_override == "hybrid":
        # Run both and merge results (Playwright wins if overlap)
        parser = LinkedInSoupParser()
        soup_data = parser.parse(html)
        playwright_data = await parse_job_posting(page)
        return {**soup_data, **{k: v for k, v in playwright_data.items() if v}}

    else:
        # Default: try Playwright first, fallback to Soup
        try:
            return await parse_job_posting(page)
        except Exception:
            parser = LinkedInSoupParser()
            return parser.parse(html)
