"""Tests for task endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_tasks_empty(client: AsyncClient, project_id: str):
    create_resp = await client.post(
        f"/api/projects/{project_id}/sprints",
        json={"goal": "test"},
    )
    sprint_id = create_resp.json()["sprint_id"]
    resp = await client.get(f"/api/sprints/{sprint_id}/tasks")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_tasks_not_found(client: AsyncClient):
    resp = await client.get("/api/sprints/nonexistent/tasks")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_task_not_found(client: AsyncClient):
    resp = await client.get("/api/tasks/nonexistent")
    assert resp.status_code == 404
