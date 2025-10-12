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

async def fetch_full_job_description(job_id: str, client: httpx.AsyncClient, parse_description: bool = True, retry_count: int = 0) -> dict:
    """
    Fetch full job description using LinkedIn's jobs-guest API with retry logic.

    Args:
        job_id (str): LinkedIn job posting ID
        client (httpx.AsyncClient): HTTP client to use
        parse_description (bool): Whether to parse with LinkedIn parser
        retry_count (int): Current retry attempt

    Returns:
        dict: Job description data or None if failed
    """
    max_retries = 3
    base_delay = 5  # Start with 5 second delay

    try:
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "accept-language": "en-US,en;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "user-agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "cache-control": "max-age=0",
        }

        print(f"🔍 Fetching job description from: {url}")
        response = await client.get(url, headers=headers, timeout=15.0, follow_redirects=True)
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

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            # Rate limited - implement exponential backoff
            if retry_count < max_retries:
                wait_time = base_delay * (2 ** retry_count) + random.uniform(0, 2)
                print(f"⏳ Rate limited (429). Waiting {wait_time:.1f}s before retry {retry_count + 1}/{max_retries}...")
                await asyncio.sleep(wait_time)
                return await fetch_full_job_description(job_id, client, parse_description, retry_count + 1)
            else:
                print(f"❌ Max retries reached for job {job_id} after rate limiting")
                return None
        else:
            print(f"❌ HTTP error fetching job {job_id}: {e.response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error fetching full description for job {job_id}: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

async def scrape_linkedin_jobs(keyword: str, location: str, pages: int = 3, fetch_full_description: bool = False):
    """
    Scrape LinkedIn job postings - EXACT implementation from Apify blog.
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
        "priority": "u=1, i",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
    }

    # Iterate over each pagination page
    for page in range(pages):
        yield {"status": "progress", "message": f"Scraping page {page + 1}/{pages}"}

        async with httpx.AsyncClient() as client:
            # Set the right pagination argument
            params["start"] = str(page * 10)

            # Perform a GET HTTP request to the target API
            response = await client.get(url, headers=headers, params=params)

        # Parse the HTML content returned by API
        soup = BeautifulSoup(response.content, "html.parser")

        # Select all <li> job posting elements
        job_li_elements = soup.select("li")

        if not job_li_elements:
            yield {"status": "progress", "message": "No listings found on this page."}
            continue

        # Iterate over them and scrape data from each of them
        for job_li_element in job_li_elements:
            # Scraping logic - EXACT from Apify blog
            link_element = job_li_element.select_one('a[data-tracking-control-name="public_jobs_jserp-result_search-card"]')
            link = link_element["href"] if link_element else None

            title_element = job_li_element.select_one("h3.base-search-card__title")
            title = title_element.text.strip() if title_element else None

            company_element = job_li_element.select_one("h4.base-search-card__subtitle")
            company = company_element.text.strip() if company_element else None

            publication_date_element = job_li_element.select_one("time.job-search-card__listdate")
            publication_date = publication_date_element["datetime"] if publication_date_element else None

            # Populate a new job posting with the scraped data
            job_posting = {
                "url": link,
                "title": title,
                "company": company,
                "publication_date": publication_date
            }

            # If fetch_full_description is True, fetch the job page directly
            if fetch_full_description and link:
                try:
                    print(f"🔍 Fetching full job page: {link}")

                    headers = {
                        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "accept-language": "en-US,en;q=0.9",
                        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    }

                    async with httpx.AsyncClient() as job_client:
                        response = await job_client.get(link, headers=headers, timeout=15.0, follow_redirects=True)
                        response.raise_for_status()

                    print(f"✅ Got job page, parsing with LinkedIn parser...")

                    # Parse the full job page HTML with the LinkedIn parser
                    from platforms.linkedin.parsers.parser import parse_linkedin_job
                    parsed_data = parse_linkedin_job(response.text)

                    if parsed_data and parsed_data.get('description'):
                        job_posting['description'] = parsed_data['description']
                        job_posting['salary'] = parsed_data.get('salary')
                        job_posting['work_type'] = parsed_data.get('work_type')
                        job_posting['employment_type'] = parsed_data.get('employment_type')
                        job_posting['applicants'] = parsed_data.get('applicants')
                        job_posting['location'] = parsed_data.get('location')
                        job_posting['posted'] = parsed_data.get('posted')
                        print(f"✅ Parsed job: {len(parsed_data.get('description', ''))} chars")
                    else:
                        print(f"⚠️ No description found in parsed data")

                    # Small delay between requests
                    await asyncio.sleep(random.uniform(2.0, 4.0))

                except Exception as e:
                    print(f"❌ Error fetching job page {link}: {e}")

            # Yield the job
            yield {
                "status": "job",
                "data": job_posting
            }

        yield {"status": "progress", "message": f"Found {len(job_li_elements)} listings on page {page + 1}"}
