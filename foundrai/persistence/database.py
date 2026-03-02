"""SQLite database connection and schema management."""

from __future__ import annotations

from pathlib import Path

import aiosqlite

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sprints (
    sprint_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    sprint_number INTEGER NOT NULL,
    goal TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'created',
    metrics_json TEXT DEFAULT '{}',
    error TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_sprints_project ON sprints(project_id);
CREATE INDEX IF NOT EXISTS idx_sprints_status ON sprints(status);

CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    sprint_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    acceptance_criteria_json TEXT DEFAULT '[]',
    assigned_to TEXT NOT NULL DEFAULT 'developer',
    priority INTEGER NOT NULL DEFAULT 3,
    status TEXT NOT NULL DEFAULT 'backlog',
    dependencies_json TEXT DEFAULT '[]',
    result_json TEXT,
    review_json TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_tasks_sprint ON tasks(sprint_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

CREATE TABLE IF NOT EXISTS messages (
    message_id TEXT PRIMARY KEY,
    sprint_id TEXT NOT NULL DEFAULT '',
    type TEXT NOT NULL,
    from_agent TEXT NOT NULL,
    to_agent TEXT,
    content TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}',
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_messages_sprint ON messages(sprint_id);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    sprint_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL DEFAULT 'code',
    file_path TEXT NOT NULL,
    content_hash TEXT NOT NULL DEFAULT '',
    size_bytes INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_artifacts_sprint ON artifacts(sprint_id);

CREATE TABLE IF NOT EXISTS events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    data_json TEXT NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);

CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    sprint_id TEXT NOT NULL,
    task_id TEXT,
    agent_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    context_json TEXT DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending',
    comment TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_approvals_sprint ON approvals(sprint_id);
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);

CREATE TABLE IF NOT EXISTS learnings (
    learning_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    sprint_id TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_learnings_project ON learnings(project_id);

CREATE TABLE IF NOT EXISTS token_usage (
    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,
    sprint_id TEXT,
    project_id TEXT,
    agent_role TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0.0,
    timestamp TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_token_usage_sprint ON token_usage(sprint_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_project ON token_usage(project_id);

CREATE TABLE IF NOT EXISTS budget_overrides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id TEXT,
    agent_role TEXT,
    budget_usd REAL NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS agent_configs (
    project_id TEXT NOT NULL,
    agent_role TEXT NOT NULL,
    autonomy_level TEXT NOT NULL DEFAULT 'notify',
    model TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (project_id, agent_role)
);

CREATE TABLE IF NOT EXISTS decision_traces (
    trace_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    task_id TEXT,
    sprint_id TEXT,
    agent_role TEXT NOT NULL,
    model TEXT,
    prompt_compressed BLOB,
    response_compressed BLOB,
    thinking TEXT,
    tool_calls_json TEXT,
    tokens_used INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0.0,
    duration_ms INTEGER DEFAULT 0,
    timestamp TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_traces_task ON decision_traces(task_id);
CREATE INDEX IF NOT EXISTS idx_traces_sprint ON decision_traces(sprint_id);

CREATE TABLE IF NOT EXISTS error_logs (
    error_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,
    sprint_id TEXT,
    agent_role TEXT NOT NULL DEFAULT '',
    error_type TEXT NOT NULL DEFAULT 'unknown',
    error_message TEXT NOT NULL DEFAULT '',
    traceback TEXT NOT NULL DEFAULT '',
    context_json TEXT DEFAULT '{}',
    suggested_fix TEXT DEFAULT '',
    timestamp TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_errors_task ON error_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_errors_sprint ON error_logs(sprint_id);
"""


class Database:
    """SQLite database connection and schema management."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Open connection and ensure schema exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        await self._connection.execute("PRAGMA journal_mode=WAL")
        await self._connection.execute("PRAGMA foreign_keys=ON")
        await self._init_schema()

    async def _init_schema(self) -> None:
        """Create tables if they don't exist."""
        await self._connection.executescript(SCHEMA_SQL)  # type: ignore[union-attr]
        await self._connection.commit()  # type: ignore[union-attr]

    async def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            await self._connection.close()

    @property
    def conn(self) -> aiosqlite.Connection:
        """Get the active connection."""
        assert self._connection is not None, "Database not connected"
        return self._connection
