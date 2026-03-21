"""Integration storage implementation."""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from foundrai.models.integration import ExternalTaskMapping, IntegrationConfig

if TYPE_CHECKING:
    from foundrai.persistence.database import Database


class IntegrationStore:
    """Storage for integration configurations and external task mappings."""

    def __init__(self, db: Database) -> None:
        """Initialize integration store."""
        self.db = db

    async def create_integration(self, integration: IntegrationConfig) -> IntegrationConfig:
        """Create a new integration configuration."""
        await self.db.conn.execute(
            """
            INSERT INTO integrations (
                id, name, project_id, config, enabled,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                integration.id,
                integration.name,
                integration.project_id,
                json.dumps(integration.config),
                int(integration.enabled),
                integration.created_at.isoformat(),
                integration.updated_at.isoformat(),
            ),
        )

        await self.db.conn.commit()
        return integration

    async def get_integration(self, integration_id: str) -> IntegrationConfig | None:
        """Get integration by ID."""
        cursor = await self.db.conn.execute(
            """
            SELECT id, name, project_id, config, enabled,
                   created_at, updated_at
            FROM integrations WHERE id = ?
        """,
            (integration_id,),
        )

        row = await cursor.fetchone()
        if not row:
            return None

        return self._row_to_integration(row)

    async def get_integration_by_name(self, name: str, project_id: str) -> IntegrationConfig | None:
        """Get integration by name and project."""
        cursor = await self.db.conn.execute(
            """
            SELECT id, name, project_id, config, enabled,
                   created_at, updated_at
            FROM integrations WHERE name = ? AND project_id = ?
        """,
            (name, project_id),
        )

        row = await cursor.fetchone()
        if not row:
            return None

        return self._row_to_integration(row)

    async def list_integrations(self, project_id: str) -> list[IntegrationConfig]:
        """List integrations for a project."""
        cursor = await self.db.conn.execute(
            """
            SELECT id, name, project_id, config, enabled,
                   created_at, updated_at
            FROM integrations WHERE project_id = ?
            ORDER BY name
        """,
            (project_id,),
        )

        rows = await cursor.fetchall()
        return [self._row_to_integration(row) for row in rows]

    async def update_integration(self, integration: IntegrationConfig) -> IntegrationConfig:
        """Update an existing integration."""
        integration.updated_at = datetime.utcnow()

        await self.db.conn.execute(
            """
            UPDATE integrations SET
                name = ?, config = ?, enabled = ?, updated_at = ?
            WHERE id = ?
        """,
            (
                integration.name,
                json.dumps(integration.config),
                int(integration.enabled),
                integration.updated_at.isoformat(),
                integration.id,
            ),
        )

        await self.db.conn.commit()
        return integration

    async def delete_integration(self, integration_id: str) -> bool:
        """Delete an integration."""
        # Also delete related task mappings
        await self.db.conn.execute(
            """
            DELETE FROM external_task_mappings
            WHERE external_system IN (
                SELECT name FROM integrations WHERE id = ?
            )
        """,
            (integration_id,),
        )

        cursor = await self.db.conn.execute(
            "DELETE FROM integrations WHERE id = ?", (integration_id,)
        )
        await self.db.conn.commit()
        return cursor.rowcount > 0

    async def create_task_mapping(self, mapping: ExternalTaskMapping) -> ExternalTaskMapping:
        """Create an external task mapping."""
        await self.db.conn.execute(
            """
            INSERT INTO external_task_mappings (
                id, task_id, external_system, external_task_id, external_url,
                last_sync, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                mapping.id,
                mapping.task_id,
                mapping.external_system,
                mapping.external_task_id,
                mapping.external_url,
                mapping.last_sync.isoformat() if mapping.last_sync else None,
                mapping.created_at.isoformat(),
            ),
        )

        await self.db.conn.commit()
        return mapping

    async def get_task_mapping(
        self, task_id: str, external_system: str
    ) -> ExternalTaskMapping | None:
        """Get task mapping for a specific task and system."""
        cursor = await self.db.conn.execute(
            """
            SELECT id, task_id, external_system, external_task_id, external_url,
                   last_sync, created_at
            FROM external_task_mappings
            WHERE task_id = ? AND external_system = ?
        """,
            (task_id, external_system),
        )

        row = await cursor.fetchone()
        if not row:
            return None

        return self._row_to_task_mapping(row)

    async def list_task_mappings(
        self, external_system: str | None = None
    ) -> list[ExternalTaskMapping]:
        """List task mappings with optional system filtering."""
        if external_system:
            cursor = await self.db.conn.execute(
                """
                SELECT id, task_id, external_system, external_task_id, external_url,
                       last_sync, created_at
                FROM external_task_mappings
                WHERE external_system = ?
                ORDER BY created_at DESC
            """,
                (external_system,),
            )
        else:
            cursor = await self.db.conn.execute("""
                SELECT id, task_id, external_system, external_task_id, external_url,
                       last_sync, created_at
                FROM external_task_mappings
                ORDER BY created_at DESC
            """)

        rows = await cursor.fetchall()
        return [self._row_to_task_mapping(row) for row in rows]

    async def update_task_mapping_sync(self, mapping_id: str, last_sync: datetime) -> bool:
        """Update the last sync time for a task mapping."""
        cursor = await self.db.conn.execute(
            """
            UPDATE external_task_mappings SET last_sync = ? WHERE id = ?
        """,
            (last_sync.isoformat(), mapping_id),
        )

        await self.db.conn.commit()
        return cursor.rowcount > 0

    async def delete_task_mapping(self, mapping_id: str) -> bool:
        """Delete a task mapping."""
        cursor = await self.db.conn.execute(
            "DELETE FROM external_task_mappings WHERE id = ?", (mapping_id,)
        )
        await self.db.conn.commit()
        return cursor.rowcount > 0

    def _row_to_integration(self, row: Any) -> IntegrationConfig:
        """Convert database row to IntegrationConfig object."""
        from foundrai.models.integration import IntegrationType

        return IntegrationConfig(
            id=row[0],
            name=row[1],
            project_id=row[2],
            integration_type=IntegrationType.SOURCE_CONTROL,  # Default, should be stored
            config=json.loads(row[3]) if row[3] else {},
            enabled=bool(row[4]),
            created_at=datetime.fromisoformat(row[5]) if isinstance(row[5], str) else row[5],
            updated_at=datetime.fromisoformat(row[6]) if isinstance(row[6], str) else row[6],
        )

    def _row_to_task_mapping(self, row: Any) -> ExternalTaskMapping:
        """Convert database row to ExternalTaskMapping object."""
        return ExternalTaskMapping(
            id=row[0],
            task_id=row[1],
            external_system=row[2],
            external_task_id=row[3],
            external_url=row[4],
            last_sync=(
                datetime.fromisoformat(row[5]) if row[5] and isinstance(row[5], str) else row[5]
            ),
            created_at=datetime.fromisoformat(row[6]) if isinstance(row[6], str) else row[6],
        )
