"""Dependency injection for API."""

from __future__ import annotations

from pathlib import Path

from foundrai.config import FoundrAIConfig
from foundrai.persistence.database import Database
from foundrai.persistence.event_log import EventLog
from foundrai.persistence.sprint_store import SprintStore

_db: Database | None = None
_config: FoundrAIConfig | None = None
_project_dir: str | None = None


def set_config(config: FoundrAIConfig) -> None:
    """Set the global config."""
    global _config
    _config = config


def get_config() -> FoundrAIConfig:
    """Get the global config."""
    assert _config is not None, "Config not set"
    return _config


def set_project_dir(project_dir: str) -> None:
    """Set the project directory for DB path resolution."""
    global _project_dir
    _project_dir = project_dir


async def get_db() -> Database:
    """Get or create the database connection."""
    global _db
    if _db is None:
        assert _config is not None, "Config not set"
        db_path = _config.persistence.sqlite_path
        if _project_dir and not Path(db_path).is_absolute():
            db_path = str(Path(_project_dir) / db_path)
        _db = Database(db_path)
        await _db.connect()
    return _db


async def get_sprint_store() -> SprintStore:
    """Get a SprintStore instance."""
    db = await get_db()
    return SprintStore(db)


async def get_event_log() -> EventLog:
    """Get an EventLog instance."""
    db = await get_db()
    return EventLog(db)


async def cleanup_db() -> None:
    """Close the database."""
    global _db
    if _db is not None:
        await _db.close()
        _db = None
