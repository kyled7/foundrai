"""ChromaDB-based vector memory for persistent learnings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from foundrai.models.learning import Learning

if TYPE_CHECKING:
    from foundrai.config import MemoryConfig


class VectorMemory:
    """ChromaDB-backed vector memory for persistent learnings."""

    def __init__(self, config: MemoryConfig) -> None:
        import chromadb

        self.client = chromadb.PersistentClient(path=config.chromadb_path)
        self.collection = self.client.get_or_create_collection(
            name="foundrai_learnings",
            metadata={"hnsw:space": "cosine"},
        )

    async def store_learning(self, learning: Learning) -> None:
        """Store a learning in vector memory."""
        self.collection.add(
            ids=[learning.id],
            documents=[learning.content],
            metadatas=[{
                "sprint_id": learning.sprint_id,
                "project_id": learning.project_id,
                "category": learning.category,
                "timestamp": learning.timestamp,
            }],
        )

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
            ))
        return learnings
