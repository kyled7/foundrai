"""Project API routes."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from foundrai.api.deps import get_db

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""


class ProjectResponse(BaseModel):
    project_id: str
    name: str
    description: str
    created_at: str
    sprint_count: int = 0
    current_sprint_id: str | None = None


@router.post("/projects", status_code=201)
async def create_project(body: ProjectCreate) -> ProjectResponse:
    """Create a new project."""
    db = await get_db()
    project_id = str(uuid.uuid4())
    await db.conn.execute(
        "INSERT INTO projects (project_id, name, description) VALUES (?, ?, ?)",
        (project_id, body.name, body.description),
    )
    await db.conn.commit()
    return ProjectResponse(
        project_id=project_id,
        name=body.name,
        description=body.description,
        created_at=datetime.utcnow().isoformat(),
        sprint_count=0,
    )


@router.get("/projects")
async def list_projects() -> dict:
    """List all projects."""
    db = await get_db()
    cursor = await db.conn.execute("SELECT * FROM projects ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    projects = []
    for row in rows:
        # Count sprints
        sc = await db.conn.execute(
            "SELECT COUNT(*) as cnt FROM sprints WHERE project_id = ?",
            (row["project_id"],),
        )
        count_row = await sc.fetchone()
        projects.append(ProjectResponse(
            project_id=row["project_id"],
            name=row["name"],
            description=row["description"],
            created_at=row["created_at"],
            sprint_count=count_row["cnt"] if count_row else 0,
        ))
    return {"projects": projects, "total": len(projects)}


@router.get("/projects/{project_id}")
async def get_project(project_id: str) -> ProjectResponse:
    """Get project details."""
    db = await get_db()
    cursor = await db.conn.execute(
        "SELECT * FROM projects WHERE project_id = ?", (project_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    sc = await db.conn.execute(
        "SELECT COUNT(*) as cnt FROM sprints WHERE project_id = ?",
        (project_id,),
    )
    count_row = await sc.fetchone()
    return ProjectResponse(
        project_id=row["project_id"],
        name=row["name"],
        description=row["description"],
        created_at=row["created_at"],
        sprint_count=count_row["cnt"] if count_row else 0,
    )
