"""Tests for database initialization."""

import pytest

from foundrai.persistence.database import Database


@pytest.mark.asyncio
async def test_database_connect(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    await db.connect()
    assert db.conn is not None
    await db.close()


@pytest.mark.asyncio
async def test_database_schema_created(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    await db.connect()

    # Check tables exist
    cursor = await db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in await cursor.fetchall()]
    assert "sprints" in tables
    assert "tasks" in tables
    assert "messages" in tables
    assert "artifacts" in tables
    assert "events" in tables

    await db.close()


@pytest.mark.asyncio
async def test_database_creates_parent_dirs(tmp_path):
    db_path = str(tmp_path / "subdir" / "nested" / "test.db")
    db = Database(db_path)
    await db.connect()
    assert db.conn is not None
    await db.close()
