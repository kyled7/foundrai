"""Tests for replay API routes."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from foundrai.api import deps
from foundrai.api.app import create_app
from foundrai.config import FoundrAIConfig, PersistenceConfig, ServerConfig


@pytest.fixture
def test_config(tmp_path):
    db_path = str(tmp_path / "test.db")
    return FoundrAIConfig(
        persistence=PersistenceConfig(sqlite_path=db_path),
        server=ServerConfig(cors_origins=["*"]),
    )


@pytest_asyncio.fixture
async def client(test_config):
    deps._db = None
    deps._config = None
    app = create_app(test_config)
    from foundrai.api.app import lifespan
    async with lifespan(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    await deps.cleanup_db()
    deps._db = None
    deps._config = None


@pytest.mark.asyncio
async def test_replay_events_empty(client: AsyncClient) -> None:
    resp = await client.post("/api/projects", json={"name": "Test"})
    assert resp.status_code == 201
    project_id = resp.json()["project_id"]

    resp = await client.post(f"/api/projects/{project_id}/sprints", json={"goal": "test"})
    sprint_id = resp.json()["sprint_id"]

    resp = await client.get(f"/api/sprints/{sprint_id}/replay")
    assert resp.status_code == 200
    data = resp.json()
    assert "events" in data
    assert isinstance(data["events"], list)


@pytest.mark.asyncio
async def test_trace_routes(client: AsyncClient) -> None:
    # Test trace endpoint returns 404 for nonexistent trace
    resp = await client.get("/api/traces/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_error_routes(client: AsyncClient) -> None:
    resp = await client.post("/api/projects", json={"name": "Test"})
    project_id = resp.json()["project_id"]
    resp = await client.post(f"/api/projects/{project_id}/sprints", json={"goal": "test"})
    sprint_id = resp.json()["sprint_id"]

    resp = await client.get(f"/api/sprints/{sprint_id}/errors")
    assert resp.status_code == 200
    assert resp.json()["errors"] == []
