# backend/api/websockets/scraping.py
import json
import uuid
from fastapi import WebSocket # type: ignore
from modules.scraping.platforms.linkedin_scraper import linkedin_scraper
from utils.session_manager import session_manager

class ScrapingWebSocketHandler:
    async def handle_scraping_websocket(self, websocket: WebSocket):
        await websocket.accept()
        try:
            data = await websocket.receive_text()
            url_data = json.loads(data)
            url = url_data.get("url")
            session_id = url_data.get("session_id")

            if not url:
                await websocket.send_text(json.dumps({
                    "type": "error", 
                    "error": "No URL provided"
                }))
                return

            # Check if we should reuse an existing session
            if not session_id:
                # Look for any valid existing session first
                valid_sessions = []
                for cookie_file in session_manager.cookie_storage_dir.glob("*.pkl"):
                    session_candidate = cookie_file.stem
                    if await session_manager.validate_session(session_candidate):
                        valid_sessions.append(session_candidate)
                
                if valid_sessions:
                    # Reuse the most recent valid session
                    session_id = valid_sessions[0]
                    await websocket.send_text(json.dumps({
                        "type": "session_found",
                        "session_id": session_id,
                        "message": f"Reusing existing session"
                    }))
                else:
                    # Create new session
                    session_id = str(uuid.uuid4())
                    await websocket.send_text(json.dumps({
                        "type": "new_session",
                        "session_id": session_id,
                        "message": "Created new session"
                    }))
            else:
                # Validate the provided session_id
                if await session_manager.validate_session(session_id):
                    await websocket.send_text(json.dumps({
                        "type": "session_found", 
                        "session_id": session_id,
                        "message": "Using provided session"
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "session_expired",
                        "session_id": session_id,
                        "message": "Session expired, creating new one"
                    }))
                    session_id = str(uuid.uuid4())

            # Scrape with the session
            result = await linkedin_scraper.scrape_job(url, session_id, websocket=websocket)
            await websocket.send_text(json.dumps(result))

        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "error", 
                "error": str(e)
            }))
        finally:
            await websocket.close()

scraping_ws_handler = ScrapingWebSocketHandler()