import asyncio
import httpx
from bs4 import BeautifulSoup

async def test_hardcoded_jobs():
    """
    Test scraper with hardcoded job posting URLs - NO PARSER, just BeautifulSoup
    """
    job_urls = [
        "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/4203017523",
        "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/4308493856",
        "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/4293626853",
        "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/4312501813",
        "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/4289670223",
        "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/4308798133",
        "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/4305760656",
        "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/4293647696",
        "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/4312886919",
        "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/4191505332",
    ]

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        for i, url in enumerate(job_urls, 1):
            yield {"status": "progress", "message": f"Fetching job {i}/{len(job_urls)}"}

            try:
                print(f"\n{'='*60}")
                print(f"🔍 Fetching job {i}: {url}")
                print(f"{'='*60}")

                response = await client.get(url, headers=headers, follow_redirects=True)
                response.raise_for_status()

                print(f"✅ Got response: {response.status_code}, {len(response.content)} bytes")

                # Use BeautifulSoup directly - NO PARSER
                soup = BeautifulSoup(response.text, "html.parser")

                # Extract whatever we can find
                title = None
                title_elem = soup.select_one("h1, h2.top-card-layout__title, .topcard__title")
                if title_elem:
                    title = title_elem.get_text(strip=True)

                company = None
                company_elem = soup.select_one("a.topcard__org-name-link, .topcard__flavor, h4")
                if company_elem:
                    company = company_elem.get_text(strip=True)

                # Get description - try multiple selectors
                description = None
                desc_selectors = [
                    "div.description__text",
                    "div.show-more-less-html__markup",
                    "section.description",
                    "div.description",
                    "article"
                ]
                for selector in desc_selectors:
                    desc_elem = soup.select_one(selector)
                    if desc_elem:
                        description = desc_elem.get_text(separator="\n", strip=True)
                        break

                # If nothing found, get all text
                if not description:
                    description = soup.get_text(separator="\n", strip=True)[:5000]

                print(f"✅ Extracted with BeautifulSoup:")
                print(f"   - Title: {title or 'N/A'}")
                print(f"   - Company: {company or 'N/A'}")
                print(f"   - Description: {len(description) if description else 0} chars")

                job_data = {
                    "url": url,
                    "title": title or "LinkedIn Job",
                    "company": company or "Unknown Company",
                    "description": description or "No description available",
                }

                yield {
                    "status": "job",
                    "data": job_data
                }

                # Small delay between requests
                await asyncio.sleep(2)

            except httpx.HTTPStatusError as e:
                print(f"❌ HTTP Error {e.response.status_code}: {url}")
                yield {"status": "progress", "message": f"❌ Job {i} - HTTP {e.response.status_code}"}
            except Exception as e:
                print(f"❌ Error: {type(e).__name__}: {e}")
                yield {"status": "progress", "message": f"❌ Job {i} - Error: {str(e)}"}

        yield {"status": "complete", "message": f"✅ Test complete! Processed {len(job_urls)} jobs"}


if __name__ == "__main__":
    async def run():
        async for result in test_hardcoded_jobs():
            if result.get("status") == "job":
                print(f"\n✅ Job ready: {result['data'].get('title')}")
            elif result.get("status") == "complete":
                print(f"\n{result.get('message')}")

    asyncio.run(run())
