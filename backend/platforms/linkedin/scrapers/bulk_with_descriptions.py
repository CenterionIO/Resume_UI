"""
Chained bulk scraper with description fetching.
Separates concerns: metadata scraping + description fetching.
"""
from .linkedin_bulk_scraper_test import scrape_linkedin_jobs_test
from .description_fetcher import fetch_job_description


async def scrape_jobs_with_descriptions(keyword: str, location: str, pages: int = 1, delay_between: float = 2.0):
    """
    Two-step process:
    1. Scrape job metadata (company, title, location, job_id) from search results
    2. Fetch full descriptions for each job using job IDs

    Args:
        keyword (str): Job search keyword
        location (str): Job location
        pages (int): Number of pages to scrape
        delay_between (float): Delay between description fetches (default 2 seconds)

    Yields:
        dict: Progress updates and complete job data (metadata + description)
    """
    # Step 1: Get job metadata and IDs
    yield {
        "status": "progress",
        "message": f"🔍 Step 1/2: Searching for '{keyword}' in '{location}'"
    }

    job_metadata_list = []

    async for result in scrape_linkedin_jobs_test(keyword, location, pages):
        # Pass through progress messages from bulk scraper
        if result.get("status") == "progress":
            yield result

        # Collect job metadata
        elif result.get("status") == "job":
            job_data = result.get("data", {})
            job_id = job_data.get("job_id")

            if job_id:
                job_metadata_list.append(job_data)

                # Notify user we found a job
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

    # Step 2: Fetch full descriptions for each job
    yield {
        "status": "progress",
        "message": f"📄 Step 2/2: Fetching full descriptions for {total_jobs} jobs..."
    }

    for index, job_metadata in enumerate(job_metadata_list, 1):
        job_id = job_metadata.get("job_id")

        yield {
            "status": "progress",
            "message": f"Fetching description {index}/{total_jobs}: {job_metadata.get('title')}"
        }

        # Fetch full description
        description_result = await fetch_job_description(
            job_id,
            delay=delay_between if index > 1 else 0  # No delay for first request
        )

        # Combine metadata from step 1 with description from step 2
        combined_data = {
            **job_metadata,  # All metadata from bulk scraper
            "description": description_result.get("description"),
            "description_status": description_result.get("status"),
        }

        # Send complete job data
        yield {
            "status": "job",
            "data": combined_data,
            "progress": f"{index}/{total_jobs}"
        }

    yield {
        "status": "complete",
        "message": f"✅ Complete! Found {total_jobs} jobs with full descriptions."
    }


if __name__ == "__main__":
    import asyncio

    async def test():
        count = 0
        async for result in scrape_jobs_with_descriptions('Software Engineer', 'Seattle', 1, delay_between=2.0):
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
                print(f"  Posted: {data.get('date_posted')}")
                print(f"  Job ID: {data.get('job_id')}")
                print(f"  Description length: {len(data.get('description', ''))} chars")
                print(f"  Description preview: {data.get('description', '')[:150]}...")

            elif status == "complete":
                print(f"\n{'='*80}")
                print(f"✅ {result.get('message')}")
                print(f"{'='*80}")

    asyncio.run(test())
