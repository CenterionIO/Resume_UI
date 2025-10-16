"""
LinkedIn Bulk Scraper
Combines search and detail fetching for LinkedIn bulk scraping operations.

Two main functions:
1. search_jobs() - Fast metadata scraping from search results
2. fetch_job_details() - Slow description fetching from individual job pages
"""
import asyncio
import httpx
import logging
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# =============================================================================
# SEARCH SCRAPER - Fast metadata collection
# =============================================================================

async def search_jobs(keyword: str, location: str, pages: int = 1):
    """
    Scrape LinkedIn job search results.

    Args:
        keyword (str): Job search keyword (e.g., "Software Engineer")
        location (str): Job location (e.g., "Seattle, WA")
        pages (int): Number of pages to scrape (default: 1)

    Yields:
        dict: Progress updates and job metadata with structure:
            - company: Company name
            - title: Job title
            - location: Job location
            - date_posted: Human-readable date (e.g., "1 week ago")
            - publication_date: ISO date string
            - job_id: LinkedIn job ID
            - job_url: Direct URL to job posting
            - guest_api_url: Guest API URL for fetching full job
            - actively_hiring: "Actively Hiring" badge (if present)
    """
    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    params = {
        "keywords": keyword,
        "location": location,
        "trk": "public_jobs_jobs-search-bar_search-submit",
        "start": "0"
    }
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
    }

    job_count = 0

    # Iterate through each page
    for page in range(pages):
        yield {"status": "progress", "message": f"Searching page {page + 1}/{pages}"}

        try:
            async with httpx.AsyncClient() as client:
                # Set pagination offset
                params["start"] = str(page * 10)

                # Fetch search results
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()

            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(response.content, "html.parser")
            job_elements = soup.select("li")

            if not job_elements:
                yield {"status": "progress", "message": f"No jobs found on page {page + 1}"}
                continue

            # Extract job data from each listing
            for job_element in job_elements:
                # Extract job URL
                link = job_element.select_one('a.base-card__full-link')
                if not link:
                    link = job_element.select_one('a[data-tracking-control-name="public_jobs_jserp-result_search-card"]')
                job_url = link["href"] if link else None

                # Extract job ID from URL
                job_id = None
                guest_api_url = None
                if job_url:
                    # Try multiple patterns to extract job ID
                    match = re.search(r'-(\d+)\?', job_url)
                    if not match:
                        match = re.search(r'-(\d+)$', job_url.split('?')[0])

                    if match:
                        job_id = match.group(1)
                        guest_api_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

                # Extract title
                title_elem = job_element.select_one("h3.base-search-card__title")
                title = title_elem.text.strip() if title_elem else None

                # Extract company
                company_elem = job_element.select_one("h4.base-search-card__subtitle > a")
                if not company_elem:
                    company_elem = job_element.select_one("h4.base-search-card__subtitle")
                company = company_elem.text.strip() if company_elem else None

                # Extract location
                location_elem = job_element.select_one("span.job-search-card__location")
                location_text = location_elem.text.strip() if location_elem else None

                # Extract posted date
                time_elem = job_element.select_one("time.job-search-card__listdate")
                date_posted = time_elem.text.strip() if time_elem else None
                publication_date = time_elem["datetime"] if time_elem and time_elem.has_attr("datetime") else None

                # Extract "Actively Hiring" badge
                hiring_elem = job_element.select_one("span.job-posting-benefits__text")
                actively_hiring = hiring_elem.text.strip() if hiring_elem else None

                # Skip if essential data is missing
                if not title or not job_id:
                    continue

                # Build job data object
                job_data = {
                    "company": company,
                    "title": title,
                    "location": location_text,
                    "date_posted": date_posted,
                    "publication_date": publication_date,
                    "job_id": job_id,
                    "job_url": job_url,
                    "guest_api_url": guest_api_url,
                    "actively_hiring": actively_hiring,
                }

                job_count += 1

                yield {
                    "status": "job",
                    "data": job_data
                }

            yield {"status": "progress", "message": f"Page {page + 1} complete - found {len(job_elements)} listings"}

        except Exception as e:
            yield {"status": "error", "message": f"Error on page {page + 1}: {str(e)}"}
            continue

    yield {"status": "complete", "message": f"Search complete! Found {job_count} jobs"}


# =============================================================================
# DETAIL SCRAPER - Slow description fetching
# =============================================================================

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
