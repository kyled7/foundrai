"""Budget management for token spending."""

from __future__ import annotations

import logging

from foundrai.models.budget import BudgetConfig, BudgetStatus
from foundrai.persistence.database import Database
from foundrai.persistence.event_log import EventLog
from foundrai.persistence.token_store import TokenStore

logger = logging.getLogger(__name__)


class BudgetManager:
    """Manages token budgets and enforcement."""

    def __init__(
        self,
        config: BudgetConfig,
        token_store: TokenStore,
        db: Database,
        event_log: EventLog,
    ) -> None:
        self.config = config
        self.token_store = token_store
        self.db = db
        self.event_log = event_log

    async def check_budget(self, sprint_id: str, agent_role: str | None = None) -> BudgetStatus:
        """Check budget status for a sprint or agent."""
        # Check for override
        budget_usd = await self._get_effective_budget(sprint_id, agent_role)

        if budget_usd <= 0:
            return BudgetStatus(
                budget_usd=0.0,
                spent_usd=0.0,
                remaining_usd=float("inf"),
                percentage_used=0.0,
                is_warning=False,
                is_exceeded=False,
            )

        if agent_role:
            spent_usd = await self.token_store.get_agent_spent(sprint_id, agent_role)
        else:
            spent_usd = await self.token_store.get_sprint_spent(sprint_id)

        remaining = max(0.0, budget_usd - spent_usd)
        pct = (spent_usd / budget_usd * 100) if budget_usd > 0 else 0.0

        status = BudgetStatus(
            budget_usd=budget_usd,
            spent_usd=spent_usd,
            remaining_usd=remaining,
            percentage_used=pct,
            is_warning=pct > 80,
            is_exceeded=pct > 100,
        )

        if status.is_warning and not status.is_exceeded:
            logger.warning(
                "Budget warning: %s %s at %.1f%% ($%.4f / $%.4f)",
                sprint_id, agent_role or "total", pct, spent_usd, budget_usd,
            )
            # Emit budget_warning event
            await self.event_log.append("budget_warning", {
                "sprint_id": sprint_id,
                "agent_role": agent_role,
                "budget_usd": budget_usd,
                "spent_usd": spent_usd,
                "percentage_used": pct,
            })
        elif status.is_exceeded:
            logger.error(
                "Budget exceeded: %s %s at %.1f%% ($%.4f / $%.4f)",
                sprint_id, agent_role or "total", pct, spent_usd, budget_usd,
            )

        return status

    async def enforce_budget(self, sprint_id: str, agent_role: str | None = None) -> bool:
        """Check if budget allows more spending. Returns False if exceeded."""
        status = await self.check_budget(sprint_id, agent_role)
        return not status.is_exceeded

    async def _get_effective_budget(self, sprint_id: str, agent_role: str | None) -> float:
        """Get effective budget, checking overrides first."""
        # Check DB overrides
        if agent_role:
            cursor = await self.db.conn.execute(
                """SELECT budget_usd FROM budget_overrides
                   WHERE sprint_id = ? AND agent_role = ?
                   ORDER BY created_at DESC LIMIT 1""",
                (sprint_id, agent_role),
            )
            row = await cursor.fetchone()
            if row:
                return float(row["budget_usd"])
            return self.config.agent_budgets.get(agent_role, 0.0)

        # Sprint-level override
        cursor = await self.db.conn.execute(
            """SELECT budget_usd FROM budget_overrides
               WHERE sprint_id = ? AND agent_role IS NULL
               ORDER BY created_at DESC LIMIT 1""",
            (sprint_id,),
        )
        row = await cursor.fetchone()
        if row:
            return float(row["budget_usd"])
        return self.config.sprint_budget_usd

    async def set_override(
        self, sprint_id: str, budget_usd: float, agent_role: str | None = None
    ) -> None:
        """Set a budget override for a sprint or agent."""
        await self.db.conn.execute(
            """INSERT INTO budget_overrides (sprint_id, agent_role, budget_usd)
               VALUES (?, ?, ?)""",
            (sprint_id, agent_role, budget_usd),
        )
        await self.db.conn.commit()
