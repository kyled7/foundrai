"""Autonomy configuration API routes."""

from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from foundrai.api.deps import get_db
from foundrai.models.autonomy_config import AutonomyProfile
from foundrai.models.enums import ActionType, AgentRoleName, AutonomyLevel

router = APIRouter()


class AutonomyConfigUpdate(BaseModel):
    """Request body for updating autonomy configuration."""

    matrix: dict[str, dict[str, str]]  # agent_role -> action_type -> autonomy_level


@router.get("/projects/{project_id}/autonomy/config")
async def get_autonomy_config(project_id: str) -> dict:
    """Get autonomy configuration for a project."""
    db = await get_db()
    cursor = await db.conn.execute(
        "SELECT agent_role, action_type, autonomy_mode FROM autonomy_config"
        " WHERE project_id = ?",
        (project_id,),
    )
    rows = await cursor.fetchall()

    # Build matrix from database rows
    matrix: dict[str, dict[str, str]] = {}
    for row in rows:
        agent_role = row["agent_role"]
        action_type = row["action_type"]
        autonomy_mode = row["autonomy_mode"]

        if agent_role not in matrix:
            matrix[agent_role] = {}
        matrix[agent_role][action_type] = autonomy_mode

    return {
        "project_id": project_id,
        "matrix": matrix,
        "updated_at": datetime.utcnow().isoformat(),
    }


@router.put("/projects/{project_id}/autonomy/config")
async def update_autonomy_config(
    project_id: str, body: AutonomyConfigUpdate
) -> dict:
    """Update autonomy configuration for a project."""
    db = await get_db()
    updated_at = datetime.utcnow().isoformat()

    # Validate matrix structure
    for agent_role, actions in body.matrix.items():
        # Validate agent role
        try:
            AgentRoleName(agent_role)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid agent role: {agent_role}"
            )

        for action_type, autonomy_mode in actions.items():
            # Validate action type
            try:
                ActionType(action_type)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid action type: {action_type}"
                )

            # Validate autonomy level
            try:
                AutonomyLevel(autonomy_mode)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid autonomy mode: {autonomy_mode}",
                )

            # Upsert the configuration
            await db.conn.execute(
                "INSERT INTO autonomy_config"
                " (project_id, agent_role, action_type, autonomy_mode, updated_at)"
                " VALUES (?, ?, ?, ?, ?)"
                " ON CONFLICT(project_id, agent_role, action_type)"
                " DO UPDATE SET autonomy_mode = ?, updated_at = ?",
                (
                    project_id,
                    agent_role,
                    action_type,
                    autonomy_mode,
                    updated_at,
                    autonomy_mode,
                    updated_at,
                ),
            )

    await db.conn.commit()

    return {
        "project_id": project_id,
        "matrix": body.matrix,
        "updated_at": updated_at,
    }


@router.get("/autonomy/profiles")
async def list_autonomy_profiles() -> dict:
    """List available autonomy profiles (builtin + custom)."""
    # Get builtin profiles
    builtin_profiles = [
        AutonomyProfile.get_full_autonomy_profile(),
        AutonomyProfile.get_supervised_profile(),
        AutonomyProfile.get_manual_review_profile(),
    ]

    # Get custom profiles from database
    db = await get_db()
    cursor = await db.conn.execute(
        "SELECT profile_id, name, description, config_json, is_default,"
        " created_at, updated_at FROM autonomy_profiles ORDER BY name"
    )
    rows = await cursor.fetchall()

    custom_profiles = [
        {
            "profile_id": row["profile_id"],
            "name": row["name"],
            "description": row["description"],
            "matrix": json.loads(row["config_json"] or "{}"),
            "is_builtin": False,
            "is_default": bool(row["is_default"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]

    # Convert builtin profiles to dict format
    builtin_dicts = [
        {
            "profile_id": p.profile_id,
            "name": p.name,
            "description": p.description,
            "matrix": {
                agent_role.value: {
                    action_type.value: autonomy_level.value
                    for action_type, autonomy_level in actions.items()
                }
                for agent_role, actions in p.matrix.items()
            },
            "is_builtin": True,
            "is_default": p.profile_id == "supervised",
            "created_at": p.created_at.isoformat(),
        }
        for p in builtin_profiles
    ]

    return {
        "profiles": builtin_dicts + custom_profiles,
        "total": len(builtin_dicts) + len(custom_profiles),
    }


@router.post("/projects/{project_id}/autonomy/apply-profile/{profile_id}")
async def apply_autonomy_profile(project_id: str, profile_id: str) -> dict:
    """Apply a preset or custom autonomy profile to a project."""
    # Check if it's a builtin profile
    builtin_profiles = {
        "full-autonomy": AutonomyProfile.get_full_autonomy_profile(),
        "supervised": AutonomyProfile.get_supervised_profile(),
        "manual-review": AutonomyProfile.get_manual_review_profile(),
    }

    profile = None
    if profile_id in builtin_profiles:
        profile = builtin_profiles[profile_id]
    else:
        # Look for custom profile in database
        db = await get_db()
        cursor = await db.conn.execute(
            "SELECT profile_id, name, description, config_json FROM"
            " autonomy_profiles WHERE profile_id = ?",
            (profile_id,),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Reconstruct profile from database
        config_json = json.loads(row["config_json"] or "{}")
        profile = AutonomyProfile(
            profile_id=row["profile_id"],
            name=row["name"],
            description=row["description"],
            matrix={
                AgentRoleName(agent_role): {
                    ActionType(action_type): AutonomyLevel(autonomy_level)
                    for action_type, autonomy_level in actions.items()
                }
                for agent_role, actions in config_json.items()
            },
        )

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Apply the profile matrix to the project
    db = await get_db()
    updated_at = datetime.utcnow().isoformat()

    # Delete existing config for this project
    await db.conn.execute(
        "DELETE FROM autonomy_config WHERE project_id = ?", (project_id,)
    )

    # Insert new configuration from profile
    for agent_role, actions in profile.matrix.items():
        for action_type, autonomy_level in actions.items():
            await db.conn.execute(
                "INSERT INTO autonomy_config"
                " (project_id, agent_role, action_type, autonomy_mode, updated_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (
                    project_id,
                    agent_role.value,
                    action_type.value,
                    autonomy_level.value,
                    updated_at,
                ),
            )

    await db.conn.commit()

    return {
        "project_id": project_id,
        "profile_id": profile.profile_id,
        "profile_name": profile.name,
        "applied_at": updated_at,
    }
