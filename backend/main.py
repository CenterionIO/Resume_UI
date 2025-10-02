# main.py - This should be your current setup
from fastapi import FastAPI, WebSocket # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from api.websockets.scraping import scraping_ws_handler

app = FastAPI(title="Resume Generator API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/scrape-progress")
async def websocket_scrape_progress(websocket: WebSocket):
    """WebSocket endpoint for scraping progress"""
    await scraping_ws_handler.handle_scraping_websocket(websocket)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Resume Generator API"}

if __name__ == "__main__":
    import uvicorn # type: ignore
    uvicorn.run(app, host="0.0.0.0", port=8000)