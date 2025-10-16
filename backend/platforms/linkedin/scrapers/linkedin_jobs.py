"""
LinkedIn Job Scraper
Fetches complete job details including full descriptions.
Can optionally parse with the sophisticated LinkedIn parser.
"""
import asyncio
import httpx
import logging
from bs4 import BeautifulSoup
from .linkedin_search import search_jobs

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


async def scrape_jobs_complete(keyword: str, location: str, pages: int = 1, delay_between: float = 2.0, use_parser: bool = False):
    """
    Complete job scraping workflow:
    1. Search for jobs (get metadata + job IDs)
    2. Fetch full details for each job
    3. Return complete job data with descriptions

    Args:
        keyword (str): Job search keyword
        location (str): Job location
        pages (int): Number of search pages to scrape
        delay_between (float): Delay between fetching individual jobs (default: 2s)
        use_parser (bool): Use sophisticated parser.py (default: False)
                          Note: Parser is designed for Playwright HTML, not guest API.
                          Set to False for guest API (bulk scraping).

    Yields:
        dict: Progress updates and complete job data
    """
    # Step 1: Search for jobs
    yield {
        "status": "progress",
        "message": f"🔍 Step 1/2: Searching for '{keyword}' in '{location}'"
    }

    job_metadata_list = []

    async for result in search_jobs(keyword, location, pages):
        # Pass through progress messages
        if result.get("status") == "progress":
            yield result

        # Collect job metadata
        elif result.get("status") == "job":
            job_data = result.get("data", {})
            job_id = job_data.get("job_id")

            if job_id:
                job_metadata_list.append(job_data)
                yield {
                    "status": "progress",
                    "message": f"✓ Found: {job_data.get('title')} at {job_data.get('company')}"
                }

    total_jobs = len(job_metadata_list)

    if total_jobs == 0:
        yield {
            "status": "complete",
            "message": "No jobs found for this search."
        }
        return

    # Step 2: Fetch full details for each job
    yield {
        "status": "progress",
        "message": f"📄 Step 2/2: Fetching details for {total_jobs} jobs..."
    }

    for index, job_metadata in enumerate(job_metadata_list, 1):
        job_id = job_metadata.get("job_id")

        yield {
            "status": "progress",
            "message": f"Fetching {index}/{total_jobs}: {job_metadata.get('title')}"
        }

        # Fetch full job details
        details = await fetch_job_details(
            job_id,
            delay=delay_between if index > 1 else 0,
            use_parser=use_parser
        )

        # Merge search metadata with fetched details
        # Prefer search metadata for title/company (cleaner), use fetched details for description
        combined_data = {
            **job_metadata,  # Search results metadata (clean title, company, location)
            "posted": details.get("posted") or job_metadata.get("date_posted"),  # Prefer parsed date
        }

        # Only add fields from details if they exist (not None)
        if details.get("description"):
            combined_data["description"] = details["description"]
        if details.get("salary"):
            combined_data["salary"] = details["salary"]
        if details.get("work_type"):
            combined_data["work_type"] = details["work_type"]
        if details.get("employment_type"):
            combined_data["employment_type"] = details["employment_type"]
        if details.get("applicants"):
            combined_data["applicants"] = details["applicants"]

        yield {
            "status": "job",
            "data": combined_data,
            "progress": f"{index}/{total_jobs}"
        }

    yield {
        "status": "complete",
        "message": f"✅ Complete! Found {total_jobs} jobs with full details."
    }


if __name__ == "__main__":
    # Test complete workflow
    async def test():
        count = 0
        async for result in scrape_jobs_complete('Software Engineer', 'Seattle', 1, delay_between=2.0):
            status = result.get("status")

            if status == "progress":
                print(f"📊 {result.get('message')}")

            elif status == "job":
                count += 1
                data = result.get("data", {})
                print(f"\n{'='*80}")
                print(f"Job {count}:")
                print(f"  Company: {data.get('company')}")
                print(f"  Title: {data.get('title')}")
                print(f"  Location: {data.get('location')}")
                print(f"  Salary: {data.get('salary')}")
                print(f"  Work Type: {data.get('work_type')}")
                print(f"  Description: {len(data.get('description', ''))} chars")

            elif status == "complete":
                print(f"\n{'='*80}")
                print(f"✅ {result.get('message')}")
                print(f"{'='*80}")

    asyncio.run(test())
