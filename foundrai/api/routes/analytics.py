"""Analytics and cost tracking API routes."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from fastapi import APIRouter
from pydantic import BaseModel, Field

from foundrai.api.deps import get_config, get_db, get_event_log, set_config
from foundrai.models.budget import BudgetConfig
from foundrai.orchestration.budget_manager import BudgetManager
from foundrai.persistence.token_store import TokenStore

router = APIRouter()


async def _get_token_store() -> TokenStore:
    db = await get_db()
    return TokenStore(db)


async def _get_budget_manager() -> BudgetManager:
    db = await get_db()
    token_store = TokenStore(db)
    event_log = await get_event_log()
    config = get_config()
    budget_config = BudgetConfig(
        sprint_budget_usd=config.budget.sprint_budget_usd,
        agent_budgets=config.budget.agent_budgets,
    )
    return BudgetManager(budget_config, token_store, db, event_log)


# --- Cost routes ---


@router.get("/sprints/{sprint_id}/cost")
async def get_sprint_cost(sprint_id: str) -> dict:
    """Get sprint cost breakdown."""
    store = await _get_token_store()
    return await store.get_sprint_usage(sprint_id)


@router.get("/projects/{project_id}/cost")
async def get_project_cost(project_id: str) -> dict:
    """Get project cost breakdown."""
    store = await _get_token_store()
    return await store.get_project_usage(project_id)


@router.get("/projects/{project_id}/agent-costs")
async def get_agent_costs(project_id: str) -> dict:
    """Get per-agent cost breakdown for a project."""
    store = await _get_token_store()
    usage = await store.get_project_usage(project_id)
    return {"project_id": project_id, "agents": usage.get("by_agent", {})}


# --- Budget routes ---


@router.get("/sprints/{sprint_id}/budget")
async def get_sprint_budget(sprint_id: str) -> dict:
    """Get sprint budget status."""
    mgr = await _get_budget_manager()
    status = await mgr.check_budget(sprint_id)
    return {
        "sprint_id": sprint_id,
        "budget_usd": status.budget_usd,
        "spent_usd": status.spent_usd,
        "remaining_usd": status.remaining_usd,
        "percentage_used": status.percentage_used,
        "is_warning": status.is_warning,
        "is_exceeded": status.is_exceeded,
    }


class BudgetOverrideRequest(BaseModel):
    budget_usd: float
    agent_role: str | None = None


@router.put("/sprints/{sprint_id}/budget")
async def set_sprint_budget(sprint_id: str, body: BudgetOverrideRequest) -> dict:
    """Override sprint or agent budget."""
    mgr = await _get_budget_manager()
    await mgr.set_override(sprint_id, body.budget_usd, body.agent_role)
    return {"status": "ok", "sprint_id": sprint_id, "budget_usd": body.budget_usd}


class BudgetConfigRequest(BaseModel):
    sprint_budget_usd: float = 0.0
    warning_threshold: float = 0.8
    model_tierdown_map: dict[str, str] = Field(default_factory=dict)
    agent_budgets: dict[str, float] = Field(default_factory=dict)


@router.get("/budget/config")
async def get_budget_config() -> dict:
    """Get current budget configuration."""
    config = get_config()
    return {
        "sprint_budget_usd": config.budget.sprint_budget_usd,
        "warning_threshold": config.budget.warning_threshold,
        "model_tierdown_map": config.budget.model_tierdown_map,
        "agent_budgets": config.budget.agent_budgets,
    }


@router.post("/budget/config")
async def save_budget_config(body: BudgetConfigRequest) -> dict:
    """Save budget configuration."""
    config = get_config()

    # Update in-memory config
    config.budget.sprint_budget_usd = body.sprint_budget_usd
    config.budget.warning_threshold = body.warning_threshold
    config.budget.model_tierdown_map = body.model_tierdown_map
    config.budget.agent_budgets = body.agent_budgets

    # Save to foundrai.yaml file
    # Find the project directory by looking for foundrai.yaml
    config_path = Path(".") / "foundrai.yaml"
    if not config_path.exists():
        # Try looking in parent directories
        current = Path(".").resolve()
        for parent in [current] + list(current.parents):
            potential_path = parent / "foundrai.yaml"
            if potential_path.exists():
                config_path = potential_path
                break

    if config_path.exists():
        # Load existing YAML
        with open(config_path) as f:
            yaml_data = yaml.safe_load(f) or {}

        # Update budget section
        if "budget" not in yaml_data:
            yaml_data["budget"] = {}
        yaml_data["budget"]["sprint_budget_usd"] = body.sprint_budget_usd
        yaml_data["budget"]["warning_threshold"] = body.warning_threshold
        yaml_data["budget"]["model_tierdown_map"] = body.model_tierdown_map
        yaml_data["budget"]["agent_budgets"] = body.agent_budgets

        # Write back to file
        with open(config_path, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    return {"status": "ok", "config": {
        "sprint_budget_usd": body.sprint_budget_usd,
        "warning_threshold": body.warning_threshold,
        "model_tierdown_map": body.model_tierdown_map,
        "agent_budgets": body.agent_budgets,
    }}


# --- Communication Graph ---


@router.get("/sprints/{sprint_id}/comm-graph")
async def get_comm_graph(sprint_id: str) -> dict:
    """Get communication graph nodes and edges for a sprint."""
    db = await get_db()
    # Get unique agents
    cursor = await db.conn.execute(
        """SELECT DISTINCT from_agent FROM messages WHERE sprint_id = ?
           UNION
           SELECT DISTINCT to_agent FROM messages WHERE sprint_id = ? AND to_agent IS NOT NULL""",
        (sprint_id, sprint_id),
    )
    agents = [row[0] for row in await cursor.fetchall() if row[0]]
    nodes = [{"id": a, "label": a.replace("_", " ").title()} for a in agents]

    # Get edges (message counts between agent pairs)
    cursor = await db.conn.execute(
        """SELECT from_agent, to_agent, COUNT(*) as count
           FROM messages
           WHERE sprint_id = ? AND to_agent IS NOT NULL
           GROUP BY from_agent, to_agent""",
        (sprint_id,),
    )
    edges = [
        {"source": row["from_agent"], "target": row["to_agent"], "count": row["count"]}
        for row in await cursor.fetchall()
    ]
    return {"nodes": nodes, "edges": edges}


# --- Sprint Comparison ---


@router.get("/projects/{project_id}/sprint-comparison")
async def get_sprint_comparison(project_id: str) -> dict:
    """Get comparison metrics across all sprints in a project."""
    db = await get_db()
    cursor = await db.conn.execute(
        """SELECT s.sprint_id, s.sprint_number, s.goal, s.status,
                  s.created_at, s.completed_at, s.metrics_json
           FROM sprints s
           WHERE s.project_id = ?
           ORDER BY s.sprint_number""",
        (project_id,),
    )
    rows = await cursor.fetchall()
    sprints = []
    for row in rows:
        metrics = json.loads(row["metrics_json"] or "{}")
        # Get token/cost data
        tc = await db.conn.execute(
            """SELECT COALESCE(SUM(total_tokens), 0) as total_tokens,
                      COALESCE(SUM(cost_usd), 0.0) as total_cost
               FROM token_usage WHERE sprint_id = ?""",
            (row["sprint_id"],),
        )
        tc_row = await tc.fetchone()

        total_tasks = metrics.get("total_tasks", 0)
        completed = metrics.get("completed_tasks", 0)
        failed = metrics.get("failed_tasks", 0)
        pass_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0

        # Duration
        duration_seconds = metrics.get("duration_seconds", 0)

        sprints.append({
            "sprint_id": row["sprint_id"],
            "sprint_number": row["sprint_number"],
            "goal": row["goal"],
            "task_count": total_tasks,
            "completed_count": completed,
            "failed_count": failed,
            "pass_rate": round(pass_rate, 1),
            "total_tokens": tc_row["total_tokens"],
            "total_cost": tc_row["total_cost"],
            "duration_seconds": duration_seconds,
        })
    return {"sprints": sprints}
