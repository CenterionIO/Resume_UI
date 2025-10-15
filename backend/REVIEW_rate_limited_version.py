import asyncio
import httpx
from bs4 import BeautifulSoup
import random
import re

def extract_job_id(url: str) -> str:
    """
    Extract job ID from LinkedIn job URL.
    """
    patterns = [
        r'/jobs/view/(\d+)',
        r'currentJobId=(\d+)',
        r'/jobPosting/(\d+)',
        r'-(\d+)(?:\?|$)',
        r'/(\d{10,})(?:/|$|\?)',
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
    THIS IS THE VERSION THAT GOT RATE LIMITED (429 errors)
    Uses: /jobs-guest/jobs/api/jobPosting/{job_id}
    """
    max_retries = 3
    base_delay = 5

    try:
        # THIS ENDPOINT CAUSED RATE LIMITING
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

        # Parse with LinkedIn parser
        if parse_description:
            from platforms.linkedin.parsers.parser import parse_linkedin_job
            parsed_data = parse_linkedin_job(response.text)
            if parsed_data:
                print(f"✅ Parsed job data with LinkedIn parser")
                print(f"   - Description: {len(parsed_data.get('description', ''))} chars")

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

        return None

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            # THIS IS WHERE IT GOT BLOCKED
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
        return None

async def scrape_linkedin_jobs(keyword: str, location: str, pages: int = 3, fetch_full_description: bool = False):
    """
    THIS VERSION GOT 1 JOB THEN RATE LIMITED
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
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        for page in range(pages):
            yield {"status": "progress", "message": f"Scraping page {page + 1}/{pages}"}

            params["start"] = str(page * 10)
            response = await client.get(url, headers=headers, params=params)

            soup = BeautifulSoup(response.content, "html.parser")
            job_li_elements = soup.select("li")

            for job_li_element in job_li_elements:
                link_element = job_li_element.select_one('a[data-tracking-control-name="public_jobs_jserp-result_search-card"]')
                link = link_element["href"] if link_element else None

                title_element = job_li_element.select_one("h3.base-search-card__title")
                title = title_element.text.strip() if title_element else None

                company_element = job_li_element.select_one("h4.base-search-card__subtitle")
                company = company_element.text.strip() if company_element else None

                job_data = {
                    "url": link,
                    "title": title,
                    "company": company,
                }

                # THIS IS WHERE IT MADE THE EXTRA REQUEST THAT GOT RATE LIMITED
                if fetch_full_description and link:
                    job_id = extract_job_id(link)
                    print(f"🔍 FETCHING FULL DESCRIPTION")
                    print(f"Job: {title}")
                    print(f"URL: {link}")
                    print(f"📝 Extracted job ID: {job_id}")

                    if job_id:
                        # THIS CALL TO THE API ENDPOINT TRIGGERED 429 AFTER FIRST JOB
                        full_description = await fetch_full_job_description(job_id, client, parse_description=True)
                        if full_description:
                            job_data.update(full_description)

                        # Delay between requests
                        await asyncio.sleep(random.uniform(3.0, 7.0))

                yield {
                    "status": "job",
                    "data": job_data
                }
