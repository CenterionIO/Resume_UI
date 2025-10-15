"""
LinkedIn Job Description Fetcher
Fetches full job descriptions from LinkedIn guest API endpoints using job IDs.
"""
import asyncio
import httpx
from bs4 import BeautifulSoup


async def fetch_job_description(job_id: str, delay: float = 2.0):
    """
    Fetch full job description from LinkedIn guest API endpoint.

    Args:
        job_id (str): LinkedIn job posting ID
        delay (float): Delay before fetching (to avoid rate limiting)

    Returns:
        dict: Job data with description or error message
    """
    # Add delay to avoid rate limiting
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

            # Parse with BeautifulSoup
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

            # If no description found with specific selectors, get all text from main content
            if not description:
                main_content = soup.select_one("main") or soup.select_one("body")
                if main_content:
                    description = main_content.get_text(separator="\n", strip=True)

            return {
                "job_id": job_id,
                "guest_api_url": guest_api_url,
                "title": title or "N/A",
                "company": company or "Unknown",
                "location": location,
                "description": description or "No description available",
                "status": "success"
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


async def fetch_multiple_descriptions(job_ids: list, delay_between: float = 2.0):
    """
    Fetch multiple job descriptions sequentially with delays.

    Args:
        job_ids (list): List of LinkedIn job posting IDs
        delay_between (float): Delay between each request (default 2 seconds)

    Yields:
        dict: Progress updates and job descriptions
    """
    total_jobs = len(job_ids)

    yield {
        "status": "started",
        "message": f"Starting to fetch {total_jobs} job descriptions..."
    }

    for index, job_id in enumerate(job_ids, 1):
        yield {
            "status": "progress",
            "message": f"Fetching job {index}/{total_jobs} (ID: {job_id})"
        }

        result = await fetch_job_description(job_id, delay=delay_between if index > 1 else 0)

        if result["status"] == "success":
            yield {
                "status": "job",
                "data": result,
                "progress": f"{index}/{total_jobs}"
            }
        else:
            yield {
                "status": "error",
                "message": f"Failed to fetch job {job_id}: {result.get('error')}",
                "job_id": job_id
            }

    yield {
        "status": "complete",
        "message": f"✅ Completed! Fetched {total_jobs} job descriptions."
    }


if __name__ == "__main__":
    # Test with a single job ID
    async def test_single():
        job_id = "4307024582"
        print(f"Testing single job fetch for ID: {job_id}\n")

        result = await fetch_job_description(job_id, delay=0)

        print(f"Status: {result['status']}")
        print(f"Title: {result.get('title')}")
        print(f"Company: {result.get('company')}")
        print(f"Location: {result.get('location')}")
        print(f"Description length: {len(result.get('description', ''))} chars")
        if result.get('description'):
            print(f"\nFirst 200 chars of description:")
            print(result['description'][:200])

    asyncio.run(test_single())
