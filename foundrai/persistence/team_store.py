"""Team storage for multi-team coordination."""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from foundrai.models.team import CrossTeamDependency, DependencyStatus, Team

if TYPE_CHECKING:
    from foundrai.persistence.database import Database


class TeamStore:
    """Storage for teams and cross-team dependencies."""

    def __init__(self, db: Database) -> None:
        """Initialize team store."""
        self.db = db

    async def create_team(self, team: Team) -> Team:
        """Create a new team."""
        await self.db.conn.execute(
            """
            INSERT INTO teams (
                id, name, description, project_id, agents, template_id,
                lead_agent, coordination_channel, sprint_config, current_sprint_id,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                team.id,
                team.name,
                team.description,
                team.project_id,
                json.dumps(team.agents),
                team.template_id,
                team.lead_agent,
                team.coordination_channel,
                json.dumps(team.sprint_config),
                team.current_sprint_id,
                team.created_at.isoformat(),
                team.updated_at.isoformat(),
            ),
        )

        await self.db.conn.commit()
        return team

    async def get_team(self, team_id: str) -> Team | None:
        """Get team by ID."""
        cursor = await self.db.conn.execute(
            """
            SELECT id, name, description, project_id, agents, template_id,
                   lead_agent, coordination_channel, sprint_config, current_sprint_id,
                   created_at, updated_at
            FROM teams WHERE id = ?
        """,
            (team_id,),
        )

        row = await cursor.fetchone()
        if not row:
            return None

        return self._row_to_team(row)

    async def list_teams(self, project_id: str | None = None) -> list[Team]:
        """List teams with optional project filtering."""
        if project_id:
            cursor = await self.db.conn.execute(
                """
                SELECT id, name, description, project_id, agents, template_id,
                       lead_agent, coordination_channel, sprint_config, current_sprint_id,
                       created_at, updated_at
                FROM teams WHERE project_id = ?
                ORDER BY created_at DESC
            """,
                (project_id,),
            )
        else:
            cursor = await self.db.conn.execute("""
                SELECT id, name, description, project_id, agents, template_id,
                       lead_agent, coordination_channel, sprint_config, current_sprint_id,
                       created_at, updated_at
                FROM teams
                ORDER BY created_at DESC
            """)

        rows = await cursor.fetchall()
        return [self._row_to_team(row) for row in rows]

    async def update_team(self, team: Team) -> Team:
        """Update an existing team."""
        team.updated_at = datetime.utcnow()

        await self.db.conn.execute(
            """
            UPDATE teams SET
                name = ?, description = ?, agents = ?, template_id = ?,
                lead_agent = ?, coordination_channel = ?, sprint_config = ?, current_sprint_id = ?,
                updated_at = ?
            WHERE id = ?
        """,
            (
                team.name,
                team.description,
                json.dumps(team.agents),
                team.template_id,
                team.lead_agent,
                team.coordination_channel,
                json.dumps(team.sprint_config),
                team.current_sprint_id,
                team.updated_at.isoformat(),
                team.id,
            ),
        )

        await self.db.conn.commit()
        return team

    async def delete_team(self, team_id: str) -> bool:
        """Delete a team."""
        cursor = await self.db.conn.execute("DELETE FROM teams WHERE id = ?", (team_id,))
        await self.db.conn.commit()
        return cursor.rowcount > 0

    async def create_dependency(self, dependency: CrossTeamDependency) -> CrossTeamDependency:
        """Create a cross-team dependency."""
        await self.db.conn.execute(
            """
            INSERT INTO cross_team_dependencies (
                id, dependent_team_id, provider_team_id, dependency_type,
                title, description, status, due_date, discussion_thread,
                resolution_notes, created_at, updated_at, resolved_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                dependency.id,
                dependency.dependent_team_id,
                dependency.provider_team_id,
                dependency.dependency_type,
                dependency.title,
                dependency.description,
                dependency.status.value,
                dependency.due_date.isoformat() if dependency.due_date else None,
                dependency.discussion_thread,
                dependency.resolution_notes,
                dependency.created_at.isoformat(),
                dependency.updated_at.isoformat(),
                dependency.resolved_at.isoformat() if dependency.resolved_at else None,
            ),
        )

        await self.db.conn.commit()
        return dependency

    async def get_dependency(self, dependency_id: str) -> CrossTeamDependency | None:
        """Get dependency by ID."""
        cursor = await self.db.conn.execute(
            """
            SELECT id, dependent_team_id, provider_team_id, dependency_type,
                   title, description, status, due_date, discussion_thread,
                   resolution_notes, created_at, updated_at, resolved_at
            FROM cross_team_dependencies WHERE id = ?
        """,
            (dependency_id,),
        )

        row = await cursor.fetchone()
        if not row:
            return None

        return self._row_to_dependency(row)

    async def list_dependencies(
        self, team_id: str | None = None, project_id: str | None = None
    ) -> list[CrossTeamDependency]:
        """List dependencies with optional filtering."""
        if team_id:
            cursor = await self.db.conn.execute(
                """
                SELECT id, dependent_team_id, provider_team_id, dependency_type,
                       title, description, status, due_date, discussion_thread,
                       resolution_notes, created_at, updated_at, resolved_at
                FROM cross_team_dependencies
                WHERE dependent_team_id = ? OR provider_team_id = ?
                ORDER BY created_at DESC
            """,
                (team_id, team_id),
            )
        elif project_id:
            cursor = await self.db.conn.execute(
                """
                SELECT d.id, d.dependent_team_id, d.provider_team_id, d.dependency_type,
                       d.title, d.description, d.status, d.due_date, d.discussion_thread,
                       d.resolution_notes, d.created_at, d.updated_at, d.resolved_at
                FROM cross_team_dependencies d
                JOIN teams t1 ON d.dependent_team_id = t1.id
                WHERE t1.project_id = ?
                ORDER BY d.created_at DESC
            """,
                (project_id,),
            )
        else:
            cursor = await self.db.conn.execute("""
                SELECT id, dependent_team_id, provider_team_id, dependency_type,
                       title, description, status, due_date, discussion_thread,
                       resolution_notes, created_at, updated_at, resolved_at
                FROM cross_team_dependencies
                ORDER BY created_at DESC
            """)

        rows = await cursor.fetchall()
        return [self._row_to_dependency(row) for row in rows]

    async def update_dependency(self, dependency: CrossTeamDependency) -> CrossTeamDependency:
        """Update a dependency."""
        dependency.updated_at = datetime.utcnow()

        await self.db.conn.execute(
            """
            UPDATE cross_team_dependencies SET
                dependency_type = ?, title = ?, description = ?, status = ?,
                due_date = ?, discussion_thread = ?, resolution_notes = ?,
                updated_at = ?, resolved_at = ?
            WHERE id = ?
        """,
            (
                dependency.dependency_type,
                dependency.title,
                dependency.description,
                dependency.status.value,
                dependency.due_date.isoformat() if dependency.due_date else None,
                dependency.discussion_thread,
                dependency.resolution_notes,
                dependency.updated_at.isoformat(),
                dependency.resolved_at.isoformat() if dependency.resolved_at else None,
                dependency.id,
            ),
        )

        await self.db.conn.commit()
        return dependency

    def _row_to_team(self, row: Any) -> Team:
        """Convert database row to Team object."""
        agents_data = json.loads(row[4]) if row[4] else []
        sprint_config_data = json.loads(row[8]) if row[8] else {}

        return Team(
            id=row[0],
            name=row[1],
            description=row[2] or "",
            project_id=row[3],
            agents=agents_data,
            template_id=row[5],
            lead_agent=row[6],
            coordination_channel=row[7],
            sprint_config=sprint_config_data,
            current_sprint_id=row[9],
            created_at=datetime.fromisoformat(row[10]) if isinstance(row[10], str) else row[10],
            updated_at=datetime.fromisoformat(row[11]) if isinstance(row[11], str) else row[11],
        )

    def _row_to_dependency(self, row: Any) -> CrossTeamDependency:
        """Convert database row to CrossTeamDependency object."""
        return CrossTeamDependency(
            id=row[0],
            dependent_team_id=row[1],
            provider_team_id=row[2],
            dependency_type=row[3],
            title=row[4],
            description=row[5] or "",
            status=DependencyStatus(row[6]),
            due_date=(
                datetime.fromisoformat(row[7]) if row[7] and isinstance(row[7], str) else row[7]
            ),
            discussion_thread=row[8],
            resolution_notes=row[9],
            created_at=datetime.fromisoformat(row[10]) if isinstance(row[10], str) else row[10],
            updated_at=datetime.fromisoformat(row[11]) if isinstance(row[11], str) else row[11],
            resolved_at=(
                datetime.fromisoformat(row[12]) if row[12] and isinstance(row[12], str) else row[12]
            ),
        )
