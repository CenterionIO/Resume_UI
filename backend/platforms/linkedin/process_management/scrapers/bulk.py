"""
LinkedIn Bulk Scraping Workflow Manager
Orchestrates the complete bulk scraping workflow:
1. Search for jobs (metadata)
2. Fetch full details for each job
3. Merge and return complete job data
"""
from platforms.linkedin.content_management.scrapers.bulk_scraper import search_jobs, fetch_job_details


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
