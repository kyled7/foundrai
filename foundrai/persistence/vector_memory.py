"""ChromaDB-based vector memory for persistent learnings."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from foundrai.models.learning import Learning

if TYPE_CHECKING:
    from foundrai.config import MemoryConfig
    from foundrai.persistence.database import Database


class VectorMemory:
    """ChromaDB-backed vector memory for persistent learnings."""

    def __init__(self, config: MemoryConfig, db: Database | None = None) -> None:
        import chromadb

        self.client = chromadb.PersistentClient(path=config.chromadb_path)
        self.collection = self.client.get_or_create_collection(
            name="foundrai_learnings",
            metadata={"hnsw:space": "cosine"},
        )
        self.db = db
        self._lock = asyncio.Lock()

    async def store_learning(self, learning: Learning) -> None:
        """Store a learning in vector memory."""
        async with self._lock:
            # Store in ChromaDB
            self.collection.add(
                ids=[learning.id],
                documents=[learning.content],
                metadatas=[{
                    "sprint_id": learning.sprint_id,
                    "project_id": learning.project_id,
                    "category": learning.category,
                    "timestamp": learning.timestamp,
                    "pinned": learning.pinned,
                    "status": learning.status,
                    "updated_at": learning.updated_at,
                }],
            )

            # Store in database if available
            if self.db:
                await self.db.conn.execute(
                    """INSERT INTO learnings
                    (learning_id, project_id, sprint_id, content, category, pinned, status, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        learning.id,
                        learning.project_id,
                        learning.sprint_id,
                        learning.content,
                        learning.category,
                        1 if learning.pinned else 0,
                        learning.status,
                        learning.updated_at,
                    ),
                )
                await self.db.conn.commit()

    async def update_learning(
        self,
        learning_id: str,
        content: str | None = None,
        pinned: bool | None = None,
        status: str | None = None
    ) -> None:
        """Update a learning in both ChromaDB and SQLite.

        Args:
            learning_id: ID of learning to update
            content: New content (if updating)
            pinned: New pinned status (if updating)
            status: New status (if updating)
        """
        from datetime import datetime, UTC

        async with self._lock:
            # Get current learning from ChromaDB
            result = self.collection.get(ids=[learning_id])
            if not result or not result['ids']:
                raise ValueError(f"Learning {learning_id} not found")

            metadata = result['metadatas'][0] if result.get('metadatas') else {}
            document = result['documents'][0] if result.get('documents') else ""

            # Update fields
            if content is not None:
                document = content
            if pinned is not None:
                metadata['pinned'] = pinned
            if status is not None:
                metadata['status'] = status
            metadata['updated_at'] = datetime.now(UTC).isoformat()

            # Update ChromaDB (delete and re-add with same ID)
            self.collection.delete(ids=[learning_id])
            self.collection.add(
                ids=[learning_id],
                documents=[document],
                metadatas=[metadata]
            )

            # Update SQLite
            if self.db:
                updates = []
                params = []

                if content is not None:
                    updates.append("content = ?")
                    params.append(content)
                if pinned is not None:
                    updates.append("pinned = ?")
                    params.append(1 if pinned else 0)
                if status is not None:
                    updates.append("status = ?")
                    params.append(status)

                if updates:
                    updates.append("updated_at = ?")
                    params.append(metadata['updated_at'])
                    params.append(learning_id)

                    await self.db.conn.execute(
                        f"UPDATE learnings SET {', '.join(updates)} WHERE learning_id = ?",
                        params
                    )
                    await self.db.conn.commit()

    async def delete_learning(self, learning_id: str) -> None:
        """Delete a learning from both ChromaDB and SQLite.

        Args:
            learning_id: ID of learning to delete
        """
        async with self._lock:
            # Delete from ChromaDB
            try:
                self.collection.delete(ids=[learning_id])
            except Exception:
                # Learning may not exist in ChromaDB, continue to delete from SQLite
                pass

            # Delete from SQLite
            if self.db:
                await self.db.conn.execute(
                    "DELETE FROM learnings WHERE learning_id = ?",
                    (learning_id,)
                )
                await self.db.conn.commit()

    async def query_relevant(
        self, query: str, k: int = 5, project_id: str | None = None
    ) -> list[Learning]:
        """Query for relevant learnings."""
        where = {"project_id": project_id} if project_id else None
        try:
            results = self.collection.query(
                query_texts=[query], n_results=k, where=where,
            )
        except Exception:
            return []

        return self._parse_results(results)

    async def get_all_learnings(
        self, project_id: str | None = None
    ) -> list[Learning]:
        """Get all stored learnings."""
        where = {"project_id": project_id} if project_id else None
        try:
            results = self.collection.get(where=where)
        except Exception:
            results = self.collection.get()

        learnings = []
        if results and results.get("ids"):
            for i, doc_id in enumerate(results["ids"]):
                meta = results["metadatas"][i] if results.get("metadatas") else {}
                doc = results["documents"][i] if results.get("documents") else ""
                learnings.append(Learning(
                    id=doc_id,
                    content=doc,
                    category=meta.get("category", "general"),
                    sprint_id=meta.get("sprint_id", ""),
                    project_id=meta.get("project_id", ""),
                    timestamp=meta.get("timestamp", ""),
                    pinned=meta.get("pinned", False),
                    status=meta.get("status", "pending"),
                    updated_at=meta.get("updated_at", meta.get("timestamp", "")),
                ))
        return learnings

    def _parse_results(self, results: dict) -> list[Learning]:
        """Parse ChromaDB query results into Learning objects."""
        learnings = []
        if not results or not results.get("ids") or not results["ids"][0]:
            return []

        for i, doc_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i] if results.get("metadatas") else {}
            doc = results["documents"][0][i] if results.get("documents") else ""
            learnings.append(Learning(
                id=doc_id,
                content=doc,
                category=meta.get("category", "general"),
                sprint_id=meta.get("sprint_id", ""),
                project_id=meta.get("project_id", ""),
                timestamp=meta.get("timestamp", ""),
                pinned=meta.get("pinned", False),
                status=meta.get("status", "pending"),
                updated_at=meta.get("updated_at", meta.get("timestamp", "")),
            ))
        return learnings
