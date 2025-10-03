# backend/api/websockets/scraping.py - REVERT TO WORKING VERSION + PARSER
import json
import uuid
import os
from datetime import datetime
from fastapi import WebSocket # type: ignore
from modules.scraping.scraper import scraping_orchestrator
from utils.session_manager import session_manager
from src.parsers.linkedin_text_parser import parse_linkedin_job_text  # Add parser import

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
            
            # Start scraping - KEEP YOUR ORIGINAL WORKING LOGIC
            job_data = await scraping_orchestrator.scrape_job_posting(
                url, 
                session_id=session_id,
                websocket=websocket
            )
            
            # NEW: Parse the job data before sending to frontend
            await websocket.send_text(json.dumps({
                "type": "progress", 
                "message": "Parsing job content..."
            }))
            
            print("🔍 Starting content parsing...")
            
            # DEBUG: Save what we're working with
            debug_dir = "debug_html"
            os.makedirs(debug_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            with open(f"{debug_dir}/raw_content_{timestamp}.txt", "w", encoding="utf-8") as f:
                f.write(job_data)
            print(f"💾 DEBUG: Saved raw content for analysis")
            
            # Parse the content with text-based parser
            parsed_job_data = parse_linkedin_job_text(job_data)
            print("✅ Content parsing completed")
            
            # Send parsed result instead of raw data
            await websocket.send_text(json.dumps({
                "type": "complete",
                "job_data": parsed_job_data,  # Now sending parsed data
                "session_id": session_id
            }))
            
        except Exception as e:
            print(f"❌ WebSocket error: {str(e)}")
            await websocket.send_text(json.dumps({
                "type": "error", 
                "error": str(e)
            }))
        finally:
            await websocket.close()

    async def find_existing_session(self):
        """Find an existing valid session"""
        for cookie_file in session_manager.cookie_storage_dir.glob("*.pkl"):
            session_id = cookie_file.stem
            if await session_manager.validate_session(session_id):
                print(f"🔍 Found existing session: {session_id}")
                return session_id
        return None

# Singleton instance
scraping_ws_handler = ScrapingWebSocketHandler()