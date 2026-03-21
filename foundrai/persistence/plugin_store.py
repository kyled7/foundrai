"""Plugin storage implementation."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from foundrai.models.plugin import Plugin, PluginType

if TYPE_CHECKING:
    from foundrai.persistence.database import Database


class PluginStore:
    """Storage for plugins."""

    def __init__(self, db: Database) -> None:
        """Initialize plugin store."""
        self.db = db

    async def create_plugin(self, plugin: Plugin) -> Plugin:
        """Create a new plugin record."""
        await self.db.conn.execute(
            """
            INSERT INTO plugins (
                id, name, version, type, metadata, config_schema,
                installed_at, enabled
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                plugin.id,
                plugin.name,
                plugin.version,
                plugin.plugin_type.value,
                plugin.model_dump_json(),
                json.dumps(plugin.configuration),
                plugin.installed_at.isoformat(),
                int(plugin.enabled),
            ),
        )

        await self.db.conn.commit()
        return plugin

    async def get_plugin(self, plugin_id: str) -> Plugin | None:
        """Get plugin by ID."""
        cursor = await self.db.conn.execute(
            """
            SELECT id, name, version, type, metadata, config_schema,
                   installed_at, enabled
            FROM plugins WHERE id = ?
        """,
            (plugin_id,),
        )

        row = await cursor.fetchone()
        if not row:
            return None

        return self._row_to_plugin(row)

    async def get_plugin_by_name(self, name: str, version: str | None = None) -> Plugin | None:
        """Get plugin by name and optional version."""
        if version:
            cursor = await self.db.conn.execute(
                """
                SELECT id, name, version, type, metadata, config_schema,
                       installed_at, enabled
                FROM plugins WHERE name = ? AND version = ?
            """,
                (name, version),
            )
        else:
            cursor = await self.db.conn.execute(
                """
                SELECT id, name, version, type, metadata, config_schema,
                       installed_at, enabled
                FROM plugins WHERE name = ?
                ORDER BY installed_at DESC LIMIT 1
            """,
                (name,),
            )

        row = await cursor.fetchone()
        if not row:
            return None

        return self._row_to_plugin(row)

    async def list_plugins(
        self, plugin_type: PluginType | None = None, enabled_only: bool = False
    ) -> list[Plugin]:
        """List plugins with optional filtering."""
        query = """
            SELECT id, name, version, type, metadata, config_schema,
                   installed_at, enabled
            FROM plugins
            WHERE 1=1
        """
        params = []

        if plugin_type:
            query += " AND type = ?"
            params.append(plugin_type.value)

        if enabled_only:
            query += " AND enabled = 1"

        query += " ORDER BY name, version"

        cursor = await self.db.conn.execute(query, params)
        rows = await cursor.fetchall()

        return [self._row_to_plugin(row) for row in rows]

    async def update_plugin(self, plugin: Plugin) -> Plugin:
        """Update an existing plugin."""
        await self.db.conn.execute(
            """
            UPDATE plugins SET
                name = ?, version = ?, type = ?, metadata = ?, config_schema = ?,
                enabled = ?
            WHERE id = ?
        """,
            (
                plugin.name,
                plugin.version,
                plugin.plugin_type.value,
                plugin.model_dump_json(),
                json.dumps(plugin.configuration),
                int(plugin.enabled),
                plugin.id,
            ),
        )

        await self.db.conn.commit()
        return plugin

    async def delete_plugin(self, plugin_id: str) -> bool:
        """Delete a plugin."""
        cursor = await self.db.conn.execute("DELETE FROM plugins WHERE id = ?", (plugin_id,))
        await self.db.conn.commit()
        return cursor.rowcount > 0

    async def toggle_plugin(self, plugin_id: str, enabled: bool) -> bool:
        """Enable or disable a plugin."""
        cursor = await self.db.conn.execute(
            """
            UPDATE plugins SET enabled = ? WHERE id = ?
        """,
            (int(enabled), plugin_id),
        )

        await self.db.conn.commit()
        return cursor.rowcount > 0

    def _row_to_plugin(self, row: Any) -> Plugin:
        """Convert database row to Plugin object."""
        # Load plugin from JSON metadata
        metadata = json.loads(row[4])
        plugin = Plugin(**metadata)

        # Override with database values that might have changed
        plugin.enabled = bool(row[7])

        return plugin
