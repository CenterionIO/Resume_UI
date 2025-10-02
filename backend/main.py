# backend/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import uuid
import os
from pathlib import Path

app = FastAPI(title="Resume Generator API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage paths (add this to your main.py)
BASE_DIR = Path(__file__).parent
SESSION_STORAGE_DIR = BASE_DIR / "storage/sessions"
COOKIE_STORAGE_DIR = BASE_DIR / "storage/cookies" 
BROWSER_PROFILES_DIR = BASE_DIR / "storage/browser_profiles"
SCREENSHOTS_DIR = BASE_DIR / "storage/screenshots"

# Ensure directories exist
os.makedirs(SESSION_STORAGE_DIR, exist_ok=True)
os.makedirs(COOKIE_STORAGE_DIR, exist_ok=True)
os.makedirs(BROWSER_PROFILES_DIR, exist_ok=True)
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

@app.websocket("/ws/scrape-progress")
async def websocket_scrape_progress(websocket: WebSocket):
    await websocket.accept()
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Receive URL from frontend
        data = await websocket.receive_text()
        url_data = json.loads(data)
        url = url_data.get('url')
        
        if not url:
            await websocket.send_text(json.dumps({"error": "No URL provided"}))
            return
        
        # Import and run the scraping function
        from linkedin_login import login_and_scrape
        job_data = await login_and_scrape(
            url, 
            websocket=websocket,
            session_id=session_id  # Pass session ID for persistence
        )
        
        await websocket.send_text(json.dumps({
            "type": "complete",
            "job_data": job_data
        }))
        
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error", 
            "error": str(e)
        }))
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)