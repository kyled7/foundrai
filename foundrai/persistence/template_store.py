"""Template storage implementation."""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from foundrai.models.template import TeamTemplate

if TYPE_CHECKING:
    from foundrai.persistence.database import Database


class TemplateStore:
    """Storage for team templates."""

    def __init__(self, db: Database) -> None:
        """Initialize template store."""
        self.db = db

    async def create_template(self, template: TeamTemplate) -> TeamTemplate:
        """Create a new team template."""
        await self.db.conn.execute(
            """
            INSERT INTO team_templates (
                id, name, description, author, version, tags,
                team_config, sprint_config, required_plugins, recommended_plugins,
                created_at, updated_at, is_public, marketplace_url, downloads, rating
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                template.id,
                template.name,
                template.description,
                template.author,
                template.version,
                json.dumps(template.tags),
                json.dumps(template.team_config),
                json.dumps(template.sprint_config),
                json.dumps(template.required_plugins),
                json.dumps(template.recommended_plugins),
                template.created_at.isoformat(),
                template.updated_at.isoformat(),
                int(template.is_public),
                template.marketplace_url,
                template.downloads,
                template.rating,
            ),
        )

        await self.db.conn.commit()
        return template

    async def get_template(self, template_id: str) -> TeamTemplate | None:
        """Get template by ID."""
        cursor = await self.db.conn.execute(
            """
            SELECT id, name, description, author, version, tags,
                   team_config, sprint_config, required_plugins, recommended_plugins,
                   created_at, updated_at, is_public, marketplace_url, downloads, rating
            FROM team_templates WHERE id = ?
        """,
            (template_id,),
        )

        row = await cursor.fetchone()
        if not row:
            return None

        return self._row_to_template(row)

    async def list_templates(
        self, author: str | None = None, public_only: bool = False
    ) -> list[TeamTemplate]:
        """List templates with optional filtering."""
        query = """
            SELECT id, name, description, author, version, tags,
                   team_config, sprint_config, required_plugins, recommended_plugins,
                   created_at, updated_at, is_public, marketplace_url, downloads, rating
            FROM team_templates
            WHERE 1=1
        """
        params = []

        if author:
            query += " AND author = ?"
            params.append(author)

        if public_only:
            query += " AND is_public = 1"

        query += " ORDER BY created_at DESC"

        cursor = await self.db.conn.execute(query, params)
        rows = await cursor.fetchall()

        return [self._row_to_template(row) for row in rows]

    async def update_template(self, template: TeamTemplate) -> TeamTemplate:
        """Update an existing template."""
        template.updated_at = datetime.utcnow()

        await self.db.conn.execute(
            """
            UPDATE team_templates SET
                name = ?, description = ?, author = ?, version = ?, tags = ?,
                team_config = ?, sprint_config = ?, required_plugins = ?, recommended_plugins = ?,
                updated_at = ?, is_public = ?, marketplace_url = ?, downloads = ?, rating = ?
            WHERE id = ?
        """,
            (
                template.name,
                template.description,
                template.author,
                template.version,
                json.dumps(template.tags),
                json.dumps(template.team_config),
                json.dumps(template.sprint_config),
                json.dumps(template.required_plugins),
                json.dumps(template.recommended_plugins),
                template.updated_at.isoformat(),
                int(template.is_public),
                template.marketplace_url,
                template.downloads,
                template.rating,
                template.id,
            ),
        )

        await self.db.conn.commit()
        return template

    async def delete_template(self, template_id: str) -> bool:
        """Delete a template."""
        cursor = await self.db.conn.execute(
            "DELETE FROM team_templates WHERE id = ?", (template_id,)
        )
        await self.db.conn.commit()
        return cursor.rowcount > 0

    async def search_templates(
        self, query: str, tags: list[str] | None = None
    ) -> list[TeamTemplate]:
        """Search templates by name/description and tags."""
        sql_query = """
            SELECT id, name, description, author, version, tags,
                   team_config, sprint_config, required_plugins, recommended_plugins,
                   created_at, updated_at, is_public, marketplace_url, downloads, rating
            FROM team_templates
            WHERE (name LIKE ? OR description LIKE ?)
        """
        params = [f"%{query}%", f"%{query}%"]

        if tags:
            for tag in tags:
                sql_query += " AND tags LIKE ?"
                params.append(f"%{tag}%")

        sql_query += " ORDER BY rating DESC, downloads DESC"

        cursor = await self.db.conn.execute(sql_query, params)
        rows = await cursor.fetchall()

        return [self._row_to_template(row) for row in rows]

    def _row_to_template(self, row: Any) -> TeamTemplate:
        """Convert database row to TeamTemplate object."""
        return TeamTemplate(
            id=row[0],
            name=row[1],
            description=row[2] or "",
            author=row[3],
            version=row[4],
            tags=json.loads(row[5]) if row[5] else [],
            team_config=json.loads(row[6]) if row[6] else {},
            sprint_config=json.loads(row[7]) if row[7] else {},
            required_plugins=json.loads(row[8]) if row[8] else [],
            recommended_plugins=json.loads(row[9]) if row[9] else [],
            created_at=datetime.fromisoformat(row[10]) if isinstance(row[10], str) else row[10],
            updated_at=datetime.fromisoformat(row[11]) if isinstance(row[11], str) else row[11],
            is_public=bool(row[12]),
            marketplace_url=row[13],
            downloads=row[14] or 0,
            rating=row[15] or 0.0,
        )
