"""
Test version of LinkedIn bulk scraper - EXACT Apify blog implementation.
Returns full DOM of each job listing from search results.
No individual job page fetching - just what's in the search results.
"""
import asyncio
import httpx
from bs4 import BeautifulSoup


async def scrape_linkedin_jobs_test(keyword: str, location: str, pages: int = 1):
    """
    Test scraper - EXACT Apify blog approach.
    Gets job listings from search and extracts structured fields using BeautifulSoup.

    Args:
        keyword (str): Job search keyword
        location (str): Job location
        pages (int): Number of pages to scrape

    Yields:
        dict: Progress updates and job data with structured fields:
            - company: Company name
            - title: Job title
            - location: Job location
            - date_posted: Human-readable posted date (e.g., "1 week ago")
            - publication_date: ISO date string
            - job_url: Direct URL to job posting
            - actively_hiring: "Actively Hiring" status (if present)
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

    # Iterate over each pagination page
    for page in range(pages):
        yield {"status": "progress", "message": f"Scraping page {page + 1}/{pages}"}

        try:
            async with httpx.AsyncClient() as client:
                # Set pagination
                params["start"] = str(page * 10)

                # Get job list - EXACTLY like Apify blog
                print(f"\n{'='*60}")
                print(f"📋 Fetching job list - Page {page + 1}")
                print(f"{'='*60}")
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                print(f"✅ Got job list: {response.status_code}")

            # Parse job list with BeautifulSoup
            soup = BeautifulSoup(response.content, "html.parser")
            job_li_elements = soup.select("li")

            if not job_li_elements:
                yield {"status": "progress", "message": "No listings found on this page."}
                continue

            print(f"Found {len(job_li_elements)} job listings on page {page + 1}")

            # Process each job listing - Extract structured fields from DOM
            for job_li_element in job_li_elements:
                # Extract job URL
                link_element = job_li_element.select_one('a.base-card__full-link')
                if not link_element:
                    link_element = job_li_element.select_one('a[data-tracking-control-name="public_jobs_jserp-result_search-card"]')
                job_url = link_element["href"] if link_element else None

                # Extract job ID from URL and build guest API URL
                job_id = None
                guest_api_url = None
                if job_url:
                    # URL format: https://www.linkedin.com/jobs/view/...-4307024582?position=...
                    # Extract the job ID (last number before query params)
                    import re
                    match = re.search(r'-(\d+)\?', job_url)
                    if not match:
                        # Try without query params (e.g., ending with just the ID)
                        match = re.search(r'-(\d+)$', job_url.split('?')[0])

                    if match:
                        job_id = match.group(1)
                        guest_api_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

                # Extract title
                title_element = job_li_element.select_one("h3.base-search-card__title")
                title = title_element.text.strip() if title_element else None

                # Extract company
                company_element = job_li_element.select_one("h4.base-search-card__subtitle > a")
                if not company_element:
                    company_element = job_li_element.select_one("h4.base-search-card__subtitle")
                company = company_element.text.strip() if company_element else None

                # Extract location
                location_element = job_li_element.select_one("span.job-search-card__location")
                location = location_element.text.strip() if location_element else None

                # Extract posted date
                time_element = job_li_element.select_one("time.job-search-card__listdate")
                date_posted = time_element.text.strip() if time_element else None
                publication_date = time_element["datetime"] if time_element and time_element.has_attr("datetime") else None

                # Extract "Actively Hiring" status
                actively_hiring_element = job_li_element.select_one("span.job-posting-benefits__text")
                actively_hiring = actively_hiring_element.text.strip() if actively_hiring_element else None

                # Skip if no title or job ID
                if not title or not job_id:
                    continue

                # Create structured job data
                job_data = {
                    "company": company,
                    "title": title,
                    "location": location,
                    "date_posted": date_posted,
                    "publication_date": publication_date,
                    "job_id": job_id,
                    "job_url": job_url,
                    "guest_api_url": guest_api_url,
                    "actively_hiring": actively_hiring,
                }

                job_count += 1

                print(f"\n✅ Job {job_count}:")
                print(f"   - Title: {title}")
                print(f"   - Company: {company}")
                print(f"   - Location: {location}")
                print(f"   - Posted: {date_posted}")
                print(f"   - Actively Hiring: {actively_hiring}")
                print(f"   - Job ID: {job_id}")
                print(f"   - Guest API URL: {guest_api_url}")

                yield {
                    "status": "job",
                    "data": job_data
                }

            yield {"status": "progress", "message": f"Completed page {page + 1} - Found {len(job_li_elements)} listings"}

        except Exception as e:
            print(f"❌ Error on page {page + 1}: {e}")
            yield {"status": "error", "message": f"Failed to load page {page + 1}: {e}"}
            continue

    yield {"status": "complete", "message": f"✅ Scraping complete! Found {job_count} jobs"}


if __name__ == "__main__":
    async def run_test():
        async for result in scrape_linkedin_jobs_test("Software Engineer", "Seattle", 1):
            if result.get("status") == "job":
                print(f"\n✅ Job: {result['data'].get('title')} at {result['data'].get('company')}")
            elif result.get("status") == "progress":
                print(f"📊 {result.get('message')}")
            elif result.get("status") == "complete":
                print(f"\n{result.get('message')}")

    asyncio.run(run_test())
