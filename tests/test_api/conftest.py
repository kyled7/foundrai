"""Shared fixtures for API tests."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from foundrai.api import deps
from foundrai.api.app import create_app
from foundrai.config import FoundrAIConfig, PersistenceConfig, ServerConfig


@pytest.fixture
def test_config(tmp_path):
    """Create a test config pointing to a temp database."""
    db_path = str(tmp_path / "test.db")
    return FoundrAIConfig(
        persistence=PersistenceConfig(sqlite_path=db_path),
        server=ServerConfig(cors_origins=["*"]),
    )


@pytest_asyncio.fixture
async def client(test_config):
    """Create an async test client."""
    # Reset deps singleton
    deps._db = None
    deps._config = None

    app = create_app(test_config)

    # Manually trigger lifespan
    from foundrai.api.app import lifespan
    async with lifespan(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    # Cleanup
    await deps.cleanup_db()
    deps._db = None
    deps._config = None


@pytest_asyncio.fixture
async def project_id(client: AsyncClient) -> str:
    """Create a test project and return its ID."""
    resp = await client.post("/api/projects", json={"name": "test-project"})
    assert resp.status_code == 201
    return resp.json()["project_id"]
