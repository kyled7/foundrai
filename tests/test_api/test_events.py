"""Tests for event and message endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_events(client: AsyncClient, project_id: str):
    create_resp = await client.post(
        f"/api/projects/{project_id}/sprints",
        json={"goal": "test"},
    )
    sprint_id = create_resp.json()["sprint_id"]
    resp = await client.get(f"/api/sprints/{sprint_id}/events")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["events"], list)


@pytest.mark.asyncio
async def test_list_events_not_found(client: AsyncClient):
    resp = await client.get("/api/sprints/nonexistent/events")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_messages(client: AsyncClient, project_id: str):
    create_resp = await client.post(
        f"/api/projects/{project_id}/sprints",
        json={"goal": "test"},
    )
    sprint_id = create_resp.json()["sprint_id"]
    resp = await client.get(f"/api/sprints/{sprint_id}/messages")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_messages_not_found(client: AsyncClient):
    resp = await client.get("/api/sprints/nonexistent/messages")
    assert resp.status_code == 404
