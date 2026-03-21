"""Artifact file storage and index."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from foundrai.persistence.database import Database


class ArtifactStore:
    """Artifact storage and indexing."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def save(self, artifact: dict) -> None:
        """Save an artifact record."""
        await self.db.conn.execute(
            """INSERT OR REPLACE INTO artifacts
            (artifact_id, sprint_id, task_id, agent_id, artifact_type,
             file_path, content_hash, size_bytes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                artifact.get("id", ""),
                artifact.get("sprint_id", ""),
                artifact.get("task_id", ""),
                artifact.get("agent_id", ""),
                artifact.get("artifact_type", "code"),
                artifact.get("file_path", ""),
                artifact.get("content_hash", ""),
                artifact.get("size_bytes", 0),
            ),
        )
        await self.db.conn.commit()

    async def get_by_sprint(self, sprint_id: str) -> list[dict]:
        """Get all artifacts for a sprint."""
        cursor = await self.db.conn.execute(
            "SELECT * FROM artifacts WHERE sprint_id = ?", (sprint_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_by_task(self, task_id: str) -> list[dict]:
        """Get all artifacts for a task."""
        cursor = await self.db.conn.execute("SELECT * FROM artifacts WHERE task_id = ?", (task_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
