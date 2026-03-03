"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from foundrai.api import deps
from foundrai.config import FoundrAIConfig


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — connect/disconnect DB."""
    # Startup
    await deps.get_db()
    yield
    # Shutdown
    await deps.cleanup_db()


def create_app(config: FoundrAIConfig | None = None) -> FastAPI:
    if config is None:
        config = FoundrAIConfig()
    """Create and configure the FastAPI application."""
    deps.set_config(config)

    app = FastAPI(
        title="FoundrAI",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    # CORS
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
        integrations,
        learnings,
        plugins,
        projects,
        replay,
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
    
    # Phase 4 routes
    app.include_router(plugins.router, prefix="/api")
    app.include_router(templates.router, prefix="/api") 
    app.include_router(teams.router, prefix="/api")
    app.include_router(integrations.router, prefix="/api")

    # WebSocket
    @app.websocket("/ws/sprints/{sprint_id}")
    async def websocket_endpoint(websocket: WebSocket, sprint_id: str) -> None:
        await websocket.accept()
        # Send handshake
        await websocket.send_json({
            "type": "connection.established",
            "data": {"sprint_id": sprint_id, "status": "connected"},
            "timestamp": "",
            "sequence": 0,
        })
        try:
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            pass

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
