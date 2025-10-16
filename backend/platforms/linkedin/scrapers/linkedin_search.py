"""
LinkedIn Search Scraper
Scrapes job search results from LinkedIn's public API.
Returns job metadata (title, company, location, job_id) without full descriptions.
"""
import asyncio
import httpx
from bs4 import BeautifulSoup
import re


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


if __name__ == "__main__":
    # Test the search functionality
    async def test():
        async for result in search_jobs("Software Engineer", "Seattle", 1):
            if result.get("status") == "job":
                data = result["data"]
                print(f"\n✅ {data.get('title')} at {data.get('company')}")
                print(f"   ID: {data.get('job_id')}")
            elif result.get("status") in ["progress", "complete"]:
                print(f"📊 {result.get('message')}")

    asyncio.run(test())
