"""Tests for VectorMemory (ChromaDB integration)."""

from __future__ import annotations

import pytest

from foundrai.config import MemoryConfig
from foundrai.models.learning import Learning
from foundrai.persistence.vector_memory import VectorMemory


@pytest.fixture
def memory(tmp_path):
    config = MemoryConfig(chromadb_path=str(tmp_path / "vectors"))
    return VectorMemory(config)


@pytest.mark.asyncio
async def test_store_and_query(memory):
    learning = Learning(
        content="Always validate user input before processing",
        category="technical",
        sprint_id="s1",
        project_id="p1",
    )
    await memory.store_learning(learning)

    results = await memory.query_relevant("input validation", k=5)
    assert len(results) == 1
    assert "validate" in results[0].content.lower()


@pytest.mark.asyncio
async def test_empty_query(memory):
    results = await memory.query_relevant("anything", k=5)
    assert results == []


@pytest.mark.asyncio
async def test_store_multiple(memory):
    for i in range(3):
        await memory.store_learning(
            Learning(
                content=f"Learning {i}: some content about topic {i}",
                category="process",
                sprint_id=f"s{i}",
                project_id="p1",
            )
        )

    results = await memory.query_relevant("topic", k=10)
    assert len(results) == 3


@pytest.mark.asyncio
async def test_project_filter(memory):
    await memory.store_learning(
        Learning(
            content="Project A learning",
            category="process",
            sprint_id="s1",
            project_id="pA",
        )
    )
    await memory.store_learning(
        Learning(
            content="Project B learning",
            category="process",
            sprint_id="s2",
            project_id="pB",
        )
    )

    results = await memory.query_relevant("learning", k=10, project_id="pA")
    assert len(results) == 1
    assert results[0].project_id == "pA"


@pytest.mark.asyncio
async def test_get_all_learnings(memory):
    for i in range(3):
        await memory.store_learning(
            Learning(
                content=f"Learning {i}",
                category="general",
                sprint_id="s1",
                project_id="p1",
            )
        )

    all_learnings = await memory.get_all_learnings()
    assert len(all_learnings) == 3


@pytest.mark.asyncio
async def test_get_all_with_project_filter(memory):
    await memory.store_learning(
        Learning(
            content="A learning",
            category="general",
            sprint_id="s1",
            project_id="p1",
        )
    )
    await memory.store_learning(
        Learning(
            content="B learning",
            category="general",
            sprint_id="s2",
            project_id="p2",
        )
    )

    result = await memory.get_all_learnings(project_id="p1")
    assert len(result) == 1
