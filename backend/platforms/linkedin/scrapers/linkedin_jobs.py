"""
LinkedIn Job Detail Scraper
Fetches individual job details from LinkedIn guest API.
Extracts title, company, location, and full description.
"""
import asyncio
import httpx
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


async def fetch_job_details(job_id: str, delay: float = 0, use_parser: bool = False):
    """
    Fetch full job details from LinkedIn guest API.

    Args:
        job_id (str): LinkedIn job posting ID
        delay (float): Delay before fetching (to avoid rate limiting)
        use_parser (bool): Whether to use sophisticated parser.py (default: False)
                          Note: Parser is designed for Playwright HTML, not guest API HTML.
                          Use False for guest API responses.

    Returns:
        dict: Complete job data with description, or error info
    """
    if delay > 0:
        await asyncio.sleep(delay)

    guest_api_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(guest_api_url, headers=headers, follow_redirects=True)
            response.raise_for_status()

        # Use sophisticated parser if requested
        if use_parser:
            from platforms.linkedin.parsers.parser import parse_linkedin_job
            parsed_data = parse_linkedin_job(response.text)

            logger.info(f"Parser returned data for job {job_id}: {parsed_data is not None}")
            if parsed_data:
                desc_length = len(parsed_data.get("description", "")) if parsed_data.get("description") else 0
                logger.info(f"Description length: {desc_length}")

                return {
                    "job_id": job_id,
                    "guest_api_url": guest_api_url,
                    "status": "success",
                    "title": parsed_data.get("title"),
                    "company": parsed_data.get("company_name"),
                    "location": parsed_data.get("location"),
                    "posted": parsed_data.get("posted"),
                    "applicants": parsed_data.get("applicants"),
                    "salary": parsed_data.get("salary"),
                    "work_type": parsed_data.get("work_type"),
                    "employment_type": parsed_data.get("employment_type"),
                    "description": parsed_data.get("description"),
                }
            else:
                logger.warning(f"Parser returned None for job {job_id}, falling back to BeautifulSoup")

        # Fallback: simple BeautifulSoup extraction
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract title
        title = None
        title_elem = soup.select_one("h1, h2.top-card-layout__title, .topcard__title")
        if title_elem:
            title = title_elem.get_text(strip=True)

        # Extract company
        company = None
        company_elem = soup.select_one("a.topcard__org-name-link, .topcard__flavor, h4")
        if company_elem:
            company = company_elem.get_text(strip=True)

        # Extract location
        location = None
        location_elem = soup.select_one("span.topcard__flavor--bullet, .job-details-jobs-unified-top-card__bullet")
        if location_elem:
            location = location_elem.get_text(strip=True)

        # Extract description - try multiple selectors
        description = None
        desc_selectors = [
            "div.description__text",
            "div.show-more-less-html__markup",
            "section.description",
            "div.description",
            "article.job-description",
        ]
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                description = desc_elem.get_text(separator="\n", strip=True)
                break

        # Fallback: get all text from main content
        if not description:
            main_content = soup.select_one("main") or soup.select_one("body")
            if main_content:
                description = main_content.get_text(separator="\n", strip=True)

        desc_length = len(description) if description else 0
        logger.info(f"BeautifulSoup fallback for job {job_id}: description length = {desc_length}")

        return {
            "job_id": job_id,
            "guest_api_url": guest_api_url,
            "status": "success",
            "title": title or "N/A",
            "company": company or "Unknown",
            "location": location,
            "description": description or "No description available",
        }

    except httpx.HTTPStatusError as e:
        return {
            "job_id": job_id,
            "guest_api_url": guest_api_url,
            "status": "error",
            "error": f"HTTP {e.response.status_code}",
            "description": None
        }
    except Exception as e:
        return {
            "job_id": job_id,
            "guest_api_url": guest_api_url,
            "status": "error",
            "error": str(e),
            "description": None
        }
