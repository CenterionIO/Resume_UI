# api/websockets/scraping.py
import json
import uuid
from fastapi import WebSocket # type: ignore
from modules.scraping.scraper import scraping_orchestrator
from utils.session_manager import session_manager

class ScrapingWebSocketHandler:
    def __init__(self):
        pass

    async def handle_scraping_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection for scraping progress"""
        await websocket.accept()
        
        try:
            # Receive data from frontend
            data = await websocket.receive_text()
            url_data = json.loads(data)
            url = url_data.get('url')
            session_id = url_data.get('session_id')
            
            print(f"🔧 WebSocket received - URL: {url}, Session ID: {session_id}")
            
            if not url:
                await websocket.send_text(json.dumps({"error": "No URL provided"}))
                return
            
            # If no session_id provided, check if we have any valid sessions
            if not session_id:
                session_id = await self.find_existing_session()
                if session_id:
                    await websocket.send_text(json.dumps({
                        "type": "session_found", 
                        "session_id": session_id,
                        "message": "Using existing session"
                    }))
            
            # If still no session_id, create new one
            if not session_id:
                session_id = str(uuid.uuid4())
                await websocket.send_text(json.dumps({
                    "type": "new_session", 
                    "session_id": session_id,
                    "message": "Created new session"
                }))
            
            print(f"🔧 FINAL SESSION ID: {session_id}")
            
            # Start scraping
            job_data = await scraping_orchestrator.scrape_job_posting(
                url, 
                session_id=session_id,
                websocket=websocket
            )
            
            await websocket.send_text(json.dumps({
                "type": "complete",
                "job_data": job_data,
                "session_id": session_id
            }))
            
        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "error", 
                "error": str(e)
            }))
        finally:
            await websocket.close()

    # api/websockets/scraping.py - Line ~45
    async def find_existing_session(self):
        """Find an existing valid session"""
        # FIX: Changed cookie_files to session_manager.cookie_storage_dir
        for cookie_file in session_manager.cookie_storage_dir.glob("*.pkl"):
            session_id = cookie_file.stem
            if await session_manager.validate_session(session_id):
                print(f"🔍 Found existing session: {session_id}")
                return session_id
        return None

# Singleton instance
scraping_ws_handler = ScrapingWebSocketHandler()