"""Agent configuration API routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from foundrai.api.deps import get_db
from foundrai.config import load_config

router = APIRouter()
logger = logging.getLogger(__name__)


class AgentConfigUpdate(BaseModel):
    autonomy_level: str | None = None
    model: str | None = None
    enabled: bool | None = None


@router.get("/projects/{project_id}/agents")
async def list_agent_configs(project_id: str) -> dict:
    """List agent configurations for a project."""
    db = await get_db()
    cursor = await db.conn.execute(
        "SELECT * FROM agent_configs WHERE project_id = ?", (project_id,)
    )
    rows = await cursor.fetchall()
    agents_list = [
        {
            "project_id": r["project_id"],
            "agent_role": r["agent_role"],
            "autonomy_level": r["autonomy_level"],
            "model": r["model"],
            "enabled": bool(r["enabled"]),
        }
        for r in rows
    ]

    # Merge roles from YAML config that aren't in DB yet
    db_roles = {a["agent_role"] for a in agents_list}
    try:
        config = load_config()
        for role, agent_cfg in config.team:
            if role not in db_roles:
                agents_list.append({
                    "project_id": project_id,
                    "agent_role": role,
                    "autonomy_level": agent_cfg.autonomy.value if hasattr(agent_cfg.autonomy, 'value') else str(agent_cfg.autonomy),
                    "model": agent_cfg.model,
                    "enabled": agent_cfg.enabled,
                })
    except Exception:
        logger.debug("Could not load config for team merge", exc_info=True)

    return {"agents": agents_list}


@router.put("/projects/{project_id}/agents/{agent_role}")
async def update_agent_config(
    project_id: str, agent_role: str, body: AgentConfigUpdate
) -> dict:
    """Update agent configuration."""
    db = await get_db()
    # Upsert
    cursor = await db.conn.execute(
        "SELECT 1 FROM agent_configs WHERE project_id = ? AND agent_role = ?",
        (project_id, agent_role),
    )
    if await cursor.fetchone():
        updates = []
        params = []
        if body.autonomy_level is not None:
            updates.append("autonomy_level = ?")
            params.append(body.autonomy_level)
        if body.model is not None:
            updates.append("model = ?")
            params.append(body.model)
        if body.enabled is not None:
            updates.append("enabled = ?")
            params.append(int(body.enabled))
        if updates:
            params.extend([project_id, agent_role])
            sql = f"UPDATE agent_configs SET {', '.join(updates)}"
            sql += " WHERE project_id = ? AND agent_role = ?"
            await db.conn.execute(sql, params)
    else:
        sql = (
            "INSERT INTO agent_configs"
            " (project_id, agent_role, autonomy_level, model, enabled)"
            " VALUES (?, ?, ?, ?, ?)"
        )
        await db.conn.execute(
            sql,
            (
                project_id,
                agent_role,
                body.autonomy_level or "notify",
                body.model or "anthropic/claude-sonnet-4-20250514",
                int(body.enabled if body.enabled is not None else True),
            ),
        )
    await db.conn.commit()
    return {"project_id": project_id, "agent_role": agent_role, "status": "updated"}
