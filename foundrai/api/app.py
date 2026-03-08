"""FastAPI application factory with WebSocket event streaming."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from foundrai.api import deps
from foundrai.config import FoundrAIConfig

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasts events to subscribers."""

    def __init__(self) -> None:
        # sprint_id -> set of connected WebSocket clients
        self._connections: dict[str, set[WebSocket]] = {}
        self._sequence: int = 0

    async def connect(self, websocket: WebSocket, sprint_id: str) -> None:
        """Register a new WebSocket connection for a sprint."""
        await websocket.accept()
        if sprint_id not in self._connections:
            self._connections[sprint_id] = set()
        self._connections[sprint_id].add(websocket)
        count = len(self._connections[sprint_id])
        logger.info("WebSocket connected for sprint %s (%d clients)", sprint_id, count)

    def disconnect(self, websocket: WebSocket, sprint_id: str) -> None:
        """Remove a disconnected WebSocket."""
        if sprint_id in self._connections:
            self._connections[sprint_id].discard(websocket)
            if not self._connections[sprint_id]:
                del self._connections[sprint_id]

    async def broadcast(self, sprint_id: str, event_type: str, data: dict) -> None:
        """Broadcast an event to all clients subscribed to a sprint."""
        clients = self._connections.get(sprint_id, set())
        if not clients:
            return

        self._sequence += 1
        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(UTC).isoformat(),
            "sequence": self._sequence,
        }

        dead: list[WebSocket] = []
        for ws in clients:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self._connections[sprint_id].discard(ws)

    async def broadcast_all(self, event_type: str, data: dict) -> None:
        """Broadcast to all connected clients (cross-sprint)."""
        sprint_id = data.get("sprint_id", "")
        if sprint_id:
            await self.broadcast(sprint_id, event_type, data)
        else:
            for sid in list(self._connections.keys()):
                await self.broadcast(sid, event_type, data)


# Global WebSocket manager instance
ws_manager = WebSocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — connect/disconnect DB, register event listener."""
    await deps.get_db()
    # Register the WebSocket broadcaster as an EventLog listener
    event_log = await deps.get_event_log()
    event_log.register_listener(_on_event)
    yield
    event_log.unregister_listener(_on_event)
    await deps.cleanup_db()


async def _on_event(event_type: str, data: dict) -> None:
    """EventLog listener that forwards events to WebSocket clients."""
    await ws_manager.broadcast_all(event_type, data)


def create_app(config: FoundrAIConfig | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if config is None:
        config = FoundrAIConfig()
    deps.set_config(config)

    app = FastAPI(
        title="FoundrAI",
        version="0.5.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    # CORS — skip in desktop mode (same-origin webview)
    if not config.desktop_mode:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.server.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # API routes
    from foundrai.api.routes import (
        agents,
        analytics,
        approvals,
        artifacts,
        errors,
        events,
        execution,
        integrations,
        learnings,
        plugins,
        projects,
        replay,
        settings,
        sprints,
        tasks,
        teams,
        templates,
        traces,
    )

    app.include_router(projects.router, prefix="/api")
    app.include_router(sprints.router, prefix="/api")
    app.include_router(tasks.router, prefix="/api")
    app.include_router(approvals.router, prefix="/api")
    app.include_router(events.router, prefix="/api")
    app.include_router(artifacts.router, prefix="/api")
    app.include_router(agents.router, prefix="/api")
    app.include_router(learnings.router, prefix="/api")
    app.include_router(analytics.router, prefix="/api")
    app.include_router(traces.router, prefix="/api")
    app.include_router(errors.router, prefix="/api")
    app.include_router(replay.router, prefix="/api")

    # Sprint execution routes
    app.include_router(execution.router, prefix="/api")

    # Settings routes (API key management for desktop mode)
    app.include_router(settings.router, prefix="/api")

    # Phase 4 routes
    app.include_router(plugins.router, prefix="/api")
    app.include_router(templates.router, prefix="/api")
    app.include_router(teams.router, prefix="/api")
    app.include_router(integrations.router, prefix="/api")

    # WebSocket endpoint with real-time event streaming
    @app.websocket("/ws/sprints/{sprint_id}")
    async def websocket_endpoint(websocket: WebSocket, sprint_id: str) -> None:
        await ws_manager.connect(websocket, sprint_id)
        # Send handshake
        await websocket.send_json({
            "type": "connection.established",
            "data": {"sprint_id": sprint_id, "status": "connected"},
            "timestamp": datetime.now(UTC).isoformat(),
            "sequence": 0,
        })
        try:
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket, sprint_id)

    # SPA catch-all route (no StaticFiles mount)
    frontend_dir = Path(__file__).parent.parent / "frontend" / "dist"

    @app.get("/{full_path:path}", response_model=None)
    async def serve_spa(full_path: str) -> FileResponse | HTMLResponse:
        """Serve frontend SPA with catch-all routing."""
        if frontend_dir.exists():
            file_path = frontend_dir / full_path
            if file_path.is_file():
                return FileResponse(str(file_path))
            index = frontend_dir / "index.html"
            if index.exists():
                return HTMLResponse(index.read_text())
        return HTMLResponse("<h1>FoundrAI</h1><p>Frontend not built.</p>")

    return app


# Module-level app instance for `uvicorn foundrai.api.app:app`
app = create_app()
