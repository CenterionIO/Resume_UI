# backend/main.py
from fastapi import FastAPI, HTTPException, WebSocket # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from pydantic import BaseModel # type: ignore

from api.websockets.scraping import scraping_ws_handler
from modules.playwright_client import fetch_and_parse_job

app = FastAPI(title="Resume Generator API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # adjust if deploying
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------
# WebSocket endpoint
# ------------------------
@app.websocket("/ws/scrape-progress")
async def websocket_scrape_progress(websocket: WebSocket):
    """WebSocket endpoint for scraping progress"""
    await scraping_ws_handler.handle_scraping_websocket(websocket)

# ------------------------
# Health check endpoint
# ------------------------
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Resume Generator API",
        "features": ["websocket", "job_parser", "playwright"]
    }

# ------------------------
# New REST parsing endpoint
# ------------------------
class ParseRequest(BaseModel):
    url: str

@app.post("/parse")
async def parse_job(req: ParseRequest):
    try:
        return await fetch_and_parse_job(req.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------
# Entrypoint
# ------------------------
if __name__ == "__main__":
    import uvicorn # type: ignore
    uvicorn.run(app, host="0.0.0.0", port=8000)
