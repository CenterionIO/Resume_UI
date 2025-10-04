import os
import json
import logging
from fastapi import FastAPI, HTTPException, Request, WebSocket  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from platforms.linkedin.parsers.playwright_client import fetch_and_parse_job  # unified client

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
async def parse_job(request: Request):
    """
    Accepts JSON body:
      {
        "url": "<linkedin_job_url>",
        "parser": "linkedin_soup" | "playwright" | "hybrid"
      }
    """
    try:
        data = await request.json()
        url = data.get("url")
        parser_override = data.get("parser", "linkedin_soup")

        if not url:
            raise HTTPException(status_code=400, detail="Missing 'url' in request body")

        logger.info(f"🔍 Parsing job: {url} using parser: {parser_override}")
        result = await fetch_and_parse_job(url, parser_override=parser_override)
        return {"status": "success", "parser": parser_override, "data": result}

    except Exception as e:
        logger.error(f"❌ Error parsing job: {e}")
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
                parser = data.get("parser", "linkedin_soup")

                if not url:
                    await websocket.send_text(json.dumps({
                        "status": "error",
                        "message": "Missing 'url' in payload"
                    }))
                    continue

                await websocket.send_text(json.dumps({
                    "status": "started",
                    "message": f"Starting parser: {parser}"
                }))

                parsed = await fetch_and_parse_job(url, parser_override=parser)

                await websocket.send_text(json.dumps({
                    "status": "complete",
                    "message": "✅ Job description ready",
                    "data": parsed
                }))

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "status": "error",
                    "message": "Invalid JSON received"
                }))
            except Exception as e:
                logger.error(f"❌ Parser error: {e}")
                await websocket.send_text(json.dumps({
                    "status": "error",
                    "message": str(e)
                }))
    except Exception as e:
        logger.warning(f"⚠️ WebSocket closed: {e}")
        await websocket.close()

# -------------------------------------------------
# Run locally
# -------------------------------------------------
if __name__ == "__main__":
    import uvicorn  # type: ignore
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
