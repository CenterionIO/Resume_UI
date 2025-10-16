import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv  # type: ignore
from fastapi import FastAPI, HTTPException, Request, WebSocket  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from pydantic import BaseModel  # type: ignore

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Import parsers and scrapers
from platforms.linkedin.parsers.single_parser import parse_linkedin_job
from platforms.linkedin.formatters.single_formatter import format_job_post
from platforms.linkedin.workflow_managers.single_manager import scrape_single_job

# Import LinkedIn workflow managers and scrapers
from platforms.linkedin.scrapers.bulk_scraper import search_jobs
from platforms.linkedin.workflow_managers.bulk_manager import scrape_jobs_complete

# -------------------------------------------------
# App Setup
# -------------------------------------------------
app = FastAPI(title="LinkedIn Parser Service", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logger Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic Model
class ParseRequest(BaseModel):
    html_content: str
    parser_type: str = "linkedin"

# Parser Registry
PARSERS = {
    "linkedin": parse_linkedin_job,
}

# -------------------------------------------------
# Healthcheck
# -------------------------------------------------
@app.get("/")
async def health():
    return {"status": "ok", "message": "LinkedIn parser backend running."}

# -------------------------------------------------
# Job Parser Endpoint
# -------------------------------------------------
@app.post("/parse")
async def parse_html(request: ParseRequest):
    """
    Accepts JSON body:
      {
        "html_content": "<html>...</html>",
        "parser_type": "linkedin"
      }
    """
    try:
        parser_type = request.parser_type.lower()
        logger.info(f"🔍 Parsing HTML with parser: {parser_type}")
        logger.info(f"HTML length: {len(request.html_content)}")

        # Validate parser type
        if parser_type not in PARSERS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid parser type: {parser_type}. Available: {list(PARSERS.keys())}"
            )

        # Parse the HTML
        parser_fn = PARSERS[parser_type]
        parsed_data = parser_fn(request.html_content)

        # Format the parsed data
        formatted_output = format_job_post(parsed_data)

        return {
            "status": "success",
            "parser": parser_type,
            "data": formatted_output,
            "metadata": parsed_data
        }

    except Exception as e:
        logger.error(f"❌ Error parsing HTML: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------
# WebSocket Endpoint (JSON-safe)
# -------------------------------------------------
@app.websocket("/ws/scrape-progress")
async def scrape_progress_socket(websocket: WebSocket):
    await websocket.accept()
    logger.info("✅ WebSocket connected")

    try:
        while True:
            raw = await websocket.receive_text()
            logger.info(f"📩 Received: {raw}")

            try:
                data = json.loads(raw)
                url = data.get("url")
                html_content = data.get("html_content")
                parser_type = data.get("parser", "linkedin")

                # Check if URL or HTML provided
                if not url and not html_content:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Missing 'url' or 'html_content' in payload"
                    }))
                    continue

                # If URL provided, fetch HTML first
                if url:
                    await websocket.send_text(json.dumps({
                        "type": "progress",
                        "message": f"🌐 Fetching job from URL..."
                    }))

                    try:
                        html_content = await scrape_single_job(url)
                        await websocket.send_text(json.dumps({
                            "type": "progress",
                            "message": f"✅ Page loaded, parsing with {parser_type}..."
                        }))
                    except Exception as e:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": f"Failed to fetch URL: {str(e)}"
                        }))
                        continue
                else:
                    await websocket.send_text(json.dumps({
                        "type": "progress",
                        "message": f"Parsing with {parser_type}..."
                    }))

                # Validate parser
                if parser_type not in PARSERS:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Invalid parser: {parser_type}"
                    }))
                    continue

                # Parse HTML
                parser_fn = PARSERS[parser_type]
                parsed_data = parser_fn(html_content)

                # Format output
                formatted_output = format_job_post(parsed_data)

                logger.info(f"✅ Parsed: {parsed_data.get('company_name')} - {parsed_data.get('title')}")
                logger.info(f"✅ Formatted output length: {len(formatted_output)}")

                await websocket.send_text(json.dumps({
                    "type": "complete",
                    "message": "✅ Job description ready",
                    "job_data": formatted_output
                }))

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON received"
                }))
            except Exception as e:
                logger.error(f"❌ Parser error: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
    except Exception as e:
        logger.warning(f"⚠️ WebSocket closed: {e}")

# -------------------------------------------------
# WebSocket Endpoint for Bulk Scraping
# -------------------------------------------------
@app.websocket("/ws/bulk-scrape")
async def bulk_scrape_socket(websocket: WebSocket):
    await websocket.accept()
    logger.info("✅ Bulk scrape WebSocket connected")

    try:
        while True:
            raw = await websocket.receive_text()
            logger.info(f"📩 Received bulk scrape request: {raw}")

            try:
                data = json.loads(raw)
                keyword = data.get("keyword")
                location = data.get("location")
                pages = data.get("pages", 1)

                # Validate inputs
                if not keyword or not location:
                    await websocket.send_text(json.dumps({
                        "status": "error",
                        "message": "Missing 'keyword' or 'location' in payload"
                    }))
                    continue

                # Start bulk scraping
                await websocket.send_text(json.dumps({
                    "status": "progress",
                    "message": f"🔍 Starting bulk scrape: '{keyword}' in '{location}' ({pages} pages)"
                }))

                job_count = 0
                async for result in scrape_jobs_complete(keyword, location, pages, delay_between=2.0, use_parser=False):
                    await websocket.send_text(json.dumps(result))

                    # Track job count
                    if result.get("status") == "job":
                        job_count += 1
                        # Format the job data if description exists
                        if result.get("data", {}).get("description"):
                            logger.info(f"✅ Job {job_count}: {result['data'].get('title')} - {result['data'].get('company')}")

                # Send completion message
                await websocket.send_text(json.dumps({
                    "status": "complete",
                    "message": f"✅ Bulk scrape complete! Found {job_count} jobs."
                }))

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "status": "error",
                    "message": "Invalid JSON received"
                }))
            except Exception as e:
                logger.error(f"❌ Bulk scrape error: {e}")
                await websocket.send_text(json.dumps({
                    "status": "error",
                    "message": str(e)
                }))
    except Exception as e:
        logger.warning(f"⚠️ Bulk scrape WebSocket closed: {e}")

# -------------------------------------------------
# WebSocket Endpoint for Testing Bulk Scraper
# -------------------------------------------------
@app.websocket("/ws/test-bulk-scraper")
async def test_bulk_scraper_socket(websocket: WebSocket):
    await websocket.accept()
    logger.info("✅ Test bulk scraper WebSocket connected")

    try:
        raw = await websocket.receive_text()
        logger.info(f"📩 Received test bulk scraper request: {raw}")

        try:
            data = json.loads(raw)
            keyword = data.get("keyword", "Software Engineer")
            location = data.get("location", "Seattle")
            pages = data.get("pages", 1)

            logger.info(f"🔍 Starting test bulk scrape: {keyword} in {location} ({pages} pages)")

            async for result in search_jobs(keyword, location, pages):
                await websocket.send_text(json.dumps(result))

        except json.JSONDecodeError:
            await websocket.send_text(json.dumps({
                "status": "error",
                "message": "Invalid JSON received"
            }))
    except Exception as e:
        logger.warning(f"⚠️ Test bulk scraper WebSocket closed: {e}")

# -------------------------------------------------
# WebSocket Endpoint for Chained Bulk Scraper with Descriptions
# -------------------------------------------------
@app.websocket("/ws/bulk-with-descriptions")
async def bulk_with_descriptions_socket(websocket: WebSocket):
    await websocket.accept()
    logger.info("✅ Bulk with descriptions WebSocket connected")

    try:
        raw = await websocket.receive_text()
        logger.info(f"📩 Received bulk with descriptions request: {raw}")

        try:
            data = json.loads(raw)
            keyword = data.get("keyword", "Software Engineer")
            location = data.get("location", "Seattle")
            pages = data.get("pages", 1)
            delay = data.get("delay", 2.0)  # Delay between description fetches

            logger.info(f"🔍 Starting chained scrape: {keyword} in {location} ({pages} pages)")

            async for result in scrape_jobs_complete(keyword, location, pages, delay_between=delay, use_parser=False):
                await websocket.send_text(json.dumps(result))

                # Log job completions
                if result.get("status") == "job":
                    data = result.get("data", {})
                    logger.info(f"✅ Complete job: {data.get('title')} - {data.get('company')}")

        except json.JSONDecodeError:
            await websocket.send_text(json.dumps({
                "status": "error",
                "message": "Invalid JSON received"
            }))
    except Exception as e:
        logger.warning(f"⚠️ Bulk with descriptions WebSocket closed: {e}")

# -------------------------------------------------
# Run locally
# -------------------------------------------------
if __name__ == "__main__":
    import uvicorn  # type: ignore
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
