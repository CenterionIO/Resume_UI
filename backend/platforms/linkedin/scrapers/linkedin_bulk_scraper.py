import asyncio
import httpx
from bs4 import BeautifulSoup
import random
import re

def extract_job_id(url: str) -> str:
    """
    Extract job ID from LinkedIn job URL.

    Handles various LinkedIn URL formats:
    - /jobs/view/123456789
    - /jobs/collections/recommended/?currentJobId=123456789
    - /jobs-guest/jobs/api/jobPosting/123456789
    - ?currentJobId=123456789
    """
    # Try different patterns
    patterns = [
        r'/jobs/view/(\d+)',           # Standard view URL
        r'currentJobId=(\d+)',          # Query parameter
        r'/jobPosting/(\d+)',           # API URL
        r'-(\d+)(?:\?|$)',              # Job ID at end of URL
        r'/(\d{10,})(?:/|$|\?)',        # Long number (job IDs are typically 10+ digits)
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            job_id = match.group(1)
            print(f"✅ Matched pattern '{pattern}' -> Job ID: {job_id}")
            return job_id

    print(f"❌ No job ID pattern matched for URL: {url}")
    return None

async def fetch_full_job_description(job_id: str, client: httpx.AsyncClient, parse_description: bool = True) -> dict:
    """
    Fetch full job description using LinkedIn's jobs-guest API.

    Args:
        job_id (str): LinkedIn job posting ID
        client (httpx.AsyncClient): HTTP client to use

    Returns:
        dict: Job description data or None if failed
    """
    try:
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "accept-language": "en-US,en;q=0.9",
            "user-agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/118.0.0.0 Safari/537.36"
            ),
        }

        print(f"🔍 Fetching job description from: {url}")
        response = await client.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()
        print(f"✅ Got response, status: {response.status_code}, length: {len(response.content)} bytes")

        # If parse_description is True, parse the full HTML through the LinkedIn parser
        if parse_description:
            from platforms.linkedin.parsers.parser import parse_linkedin_job
            parsed_data = parse_linkedin_job(response.text)
            if parsed_data:
                print(f"✅ Parsed job data with LinkedIn parser")
                print(f"   - Description: {len(parsed_data.get('description', ''))} chars")
                print(f"   - Salary: {parsed_data.get('salary', 'N/A')}")
                print(f"   - Work Type: {parsed_data.get('work_type', 'N/A')}")
                print(f"   - Employment Type: {parsed_data.get('employment_type', 'N/A')}")
                print(f"   - Applicants: {parsed_data.get('applicants', 'N/A')}")

                result = {}
                if parsed_data.get('description'):
                    result['description'] = parsed_data['description']
                if parsed_data.get('salary'):
                    result['salary'] = parsed_data['salary']
                if parsed_data.get('work_type'):
                    result['work_type'] = parsed_data['work_type']
                if parsed_data.get('employment_type'):
                    result['employment_type'] = parsed_data['employment_type']
                if parsed_data.get('applicants'):
                    result['applicants_detail'] = parsed_data['applicants']

                return result if result else None

        soup = BeautifulSoup(response.content, "html.parser")

        # Try multiple selectors in order of preference
        selectors = [
            "div.description__text",
            "div.show-more-less-html__markup",
            "section.description",
            "div.description",
            "article.job-description",
            "div[class*='description']",
            "section[class*='description']"
        ]

        for selector in selectors:
            description_element = soup.select_one(selector)
            if description_element:
                description_text = description_element.get_text(separator="\n", strip=True)
                print(f"✅ Found description using selector '{selector}' - {len(description_text)} chars")
                return {
                    "description": description_text,
                    "description_html": str(description_element)
                }

        # If no specific description element found, look for any substantial text
        print(f"⚠️ No description found with standard selectors, trying fallback...")

        # Try to find the main content area
        main_content = soup.select_one("main") or soup.select_one("body")
        if main_content:
            all_text = main_content.get_text(separator="\n", strip=True)
            if len(all_text) > 200:  # If we found substantial content
                print(f"✅ Using fallback content - {len(all_text)} chars")
                return {
                    "description": all_text[:5000],  # Limit to first 5000 chars
                    "description_html": str(main_content)
                }

        print(f"❌ No description content found for job {job_id}")
        return None

    except Exception as e:
        print(f"❌ Error fetching full description for job {job_id}: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

async def scrape_linkedin_jobs(keyword: str, location: str, pages: int = 3, fetch_full_description: bool = False):
    """
    Scrape LinkedIn job postings from the public AJAX endpoint.

    Args:
        keyword (str): Job search keyword (e.g., "AI Engineer")
        location (str): Job location (e.g., "United States")
        pages (int): Number of result pages to scrape
        fetch_full_description (bool): Whether to fetch full job descriptions (slower but more detailed)

    Yields:
        dict: Parsed job postings or progress updates
            - status: 'job' | 'progress' | 'error'
            - data (if status='job'): {url, title, company, location, publication_date, description (optional), description_html (optional)}
            - message (if status='progress' | 'error'): Progress or error message
    """

    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/118.0.0.0 Safari/537.36"
        ),
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        for page in range(pages):
            yield {"status": "progress", "message": f"Scraping page {page + 1}/{pages}"}

            params = {
                "keywords": keyword,
                "location": location,
                "trk": "public_jobs_jobs-search-bar_search-submit",
                "start": str(page * 10),
            }

            for attempt in range(3):
                try:
                    response = await client.get(base_url, headers=headers, params=params)
                    response.raise_for_status()
                    break
                except Exception as e:
                    if attempt < 2:
                        yield {"status": "progress", "message": f"Retry {attempt + 1}/3 due to {e}"}
                        await asyncio.sleep(2)
                    else:
                        yield {"status": "error", "message": f"Failed to load page {page + 1}: {e}"}
                        return

            soup = BeautifulSoup(response.content, "html.parser")
            job_li_elements = soup.select("li")

            if not job_li_elements:
                yield {"status": "progress", "message": "No listings found on this page."}
                continue

            for job_li_element in job_li_elements:
                link_element = job_li_element.select_one(
                    'a[data-tracking-control-name="public_jobs_jserp-result_search-card"]'
                )
                link = link_element["href"].strip() if link_element else None
                if link and link.startswith("/"):
                    link = f"https://www.linkedin.com{link}"

                title_element = job_li_element.select_one("h3.base-search-card__title")
                title = title_element.text.strip() if title_element else None

                company_element = job_li_element.select_one("h4.base-search-card__subtitle")
                company = company_element.text.strip() if company_element else None

                location_element = job_li_element.select_one("span.job-search-card__location")
                job_location = location_element.text.strip() if location_element else None

                # Extract publication date - can be either datetime or relative text
                publication_date_element = job_li_element.select_one("time.job-search-card__listdate")
                publication_date = None
                posted_date_text = None
                if publication_date_element:
                    publication_date = publication_date_element.get("datetime")
                    posted_date_text = publication_date_element.text.strip()

                # Extract applicant count
                applicants_element = job_li_element.select_one("span.job-search-card__listdate--new")
                if not applicants_element:
                    applicants_element = job_li_element.select_one("li.job-search-card__listitem")

                applicants = None
                if applicants_element:
                    applicants_text = applicants_element.text.strip()
                    # Look for patterns like "10 applicants", "Over 100 applicants", etc.
                    if "applicant" in applicants_text.lower():
                        applicants = applicants_text

                if not title and not link:
                    continue

                job_data = {
                    "url": link,
                    "title": title,
                    "company": company,
                    "location": job_location,
                    "publication_date": publication_date,
                    "posted_date_text": posted_date_text,  # e.g., "2 days ago"
                    "applicants": applicants,  # e.g., "50 applicants"
                }

                # Optionally fetch full job description
                if fetch_full_description and link:
                    job_id = extract_job_id(link)
                    print(f"🔍 Attempting to extract job ID from URL: {link}")
                    print(f"📝 Extracted job ID: {job_id}")
                    if job_id:
                        yield {"status": "progress", "message": f"Fetching full description for: {title}"}
                        full_description = await fetch_full_job_description(job_id, client)
                        if full_description:
                            print(f"✅ Successfully fetched description for {title} ({len(full_description.get('description', ''))} chars)")
                            job_data.update(full_description)
                        else:
                            print(f"⚠️ No description returned for {title}")
                        await asyncio.sleep(random.uniform(0.5, 1.5))  # Small delay between detail fetches
                    else:
                        print(f"❌ Could not extract job ID from URL: {link}")

                yield {
                    "status": "job",
                    "data": job_data
                }

            yield {"status": "progress", "message": f"Found {len(job_li_elements)} listings on page {page + 1}"}
            await asyncio.sleep(random.uniform(1.5, 3.5))
