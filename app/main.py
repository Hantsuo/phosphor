"""
FastAPI server for PHOSPHOR BBS terminal.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import db
from . import session as session_module
from . import presence
from . import boards
from . import screens

logger = logging.getLogger(__name__)

app = FastAPI(title="PHOSPHOR BBS", version="0.1.0")

# Mount static files
static_path = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/healthz")
async def healthz() -> dict:
    """
    Health check endpoint.
    """
    return {"ok": True, "callers": presence.get_online_count()}

@app.get("/")
async def index() -> FileResponse:
    """
    Serve the terminal client HTML.
    """
    return FileResponse(static_path / "index.html", media_type="text/html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for terminal sessions.
    """
    # Accept connection
    await websocket.accept()
    
    # Check for fast parameter
    fast = websocket.query_params.get("fast") == "1"
    guest = websocket.query_params.get("guest") == "1"
    
    # Create session
    session = session_module.Session(fast=fast)
    conn = db.connect()
    boards.seed(conn)
    
    try:
        # Send initial boot frame, or land straight on the menu for guests
        if guest:
            first = session.login_guest(conn)
            deep = websocket.query_params.get("board")
            if deep:
                target = boards.board(conn, deep)
                if target:
                    session.state = session_module.SessionState.BOARD_VIEW
                    session.board_id = target["id"]
                    first = screens.board_view(target, boards.recent(conn, target["id"]))
        else:
            first = session._render_boot()
        await websocket.send_text(json.dumps({
            "t": "frame",
            "d": first,
        }))
        
        # Main message loop
        while True:
            # Check idle timeout
            if session.check_idle():
                await websocket.send_text(json.dumps({
                    "t": "frame",
                    "d": "carrier lost",
                }))
                break
            
            # Receive message
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_text(json.dumps({"t": "ping"}))
                continue
            
            # Parse message
            try:
                msg = json.loads(data)
                msg_type = msg.get("t")
                msg_data = msg.get("d")
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Invalid message: {data}")
                continue
            
            # Handle key press
            if msg_type == "key" and isinstance(msg_data, str):
                frame = await session.handle_key(conn, msg_data)
                
                if frame == "carrier lost":
                    # Disconnect
                    await websocket.send_text(json.dumps({
                        "t": "frame",
                        "d": "carrier lost",
                    }))
                    break
                elif frame:
                    # Send updated frame
                    await websocket.send_text(json.dumps({
                        "t": "frame",
                        "d": frame,
                    }))
            else:
                logger.warning(f"Unknown message type: {msg_type}")
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
    finally:
        # Clean up
        session.disconnect()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)