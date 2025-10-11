from fastapi import APIRouter, Query, WebSocket
import asyncio
import json
from platforms.linkedin.scrapers.linkedin_bulk_scraper import scrape_linkedin_jobs

router = APIRouter(prefix="", tags=["LinkedIn Bulk"])

async def linkedin_bulk_search(keyword: str, location: str, pages: int, websocket: WebSocket, fetch_full_description: bool = True):
    """
    Performs a bulk search for LinkedIn jobs and sends progress over a WebSocket.

    Args:
        keyword (str): Job search keyword.
        location (str): Job search location.
        pages (int): Number of pages to scrape.
        websocket (WebSocket): The WebSocket to send progress updates to.
        fetch_full_description (bool): Whether to fetch full job descriptions (default: True)
    """
    try:
        job_count = 0
        async for result in scrape_linkedin_jobs(keyword, location, pages, fetch_full_description=fetch_full_description):
            await websocket.send_text(json.dumps(result))

            # Track job count
            if result.get("status") == "job":
                job_count += 1

            if result.get("status") != "progress":
                await asyncio.sleep(0.1)  # Small delay to prevent overwhelming the client

        # Send summary at the end
        await websocket.send_text(json.dumps({
            "status": "progress",
            "message": f"✅ Scraping complete! Found {job_count} job postings."
        }))

    except Exception as e:
        await websocket.send_text(json.dumps({
            "status": "error",
            "message": f"An unexpected error occurred: {e}"
        }))
