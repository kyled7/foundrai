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
    resolved_at TEXT,
    expires_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_approvals_sprint ON approvals(sprint_id);
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);

CREATE TABLE IF NOT EXISTS learnings (
    learning_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    sprint_id TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
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

CREATE TABLE IF NOT EXISTS budget_config (
    config_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT,
    agent_role TEXT,
    tier_down_map_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_budget_config_project ON budget_config(project_id);
CREATE INDEX IF NOT EXISTS idx_budget_config_agent ON budget_config(agent_role);

CREATE TABLE IF NOT EXISTS agent_configs (
    project_id TEXT NOT NULL,
    agent_role TEXT NOT NULL,
    autonomy_level TEXT NOT NULL DEFAULT 'notify',
    model TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (project_id, agent_role)
);

CREATE TABLE IF NOT EXISTS autonomy_config (
    project_id TEXT NOT NULL,
    agent_role TEXT NOT NULL,
    action_type TEXT NOT NULL,
    autonomy_mode TEXT NOT NULL DEFAULT 'notify',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (project_id, agent_role, action_type)
);
CREATE INDEX IF NOT EXISTS idx_autonomy_config_project ON autonomy_config(project_id);
CREATE INDEX IF NOT EXISTS idx_autonomy_config_agent ON autonomy_config(agent_role);

CREATE TABLE IF NOT EXISTS autonomy_profiles (
    profile_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    config_json TEXT NOT NULL DEFAULT '{}',
    is_default INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_autonomy_profiles_name ON autonomy_profiles(name);
CREATE INDEX IF NOT EXISTS idx_autonomy_profiles_default ON autonomy_profiles(is_default);

CREATE TABLE IF NOT EXISTS agent_trust_scores (
    project_id TEXT NOT NULL,
    agent_role TEXT NOT NULL,
    action_type TEXT NOT NULL,
    trust_score REAL NOT NULL DEFAULT 0.5,
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    last_updated TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (project_id, agent_role, action_type)
);
CREATE INDEX IF NOT EXISTS idx_trust_scores_project ON agent_trust_scores(project_id);
CREATE INDEX IF NOT EXISTS idx_trust_scores_agent ON agent_trust_scores(agent_role);

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

CREATE TABLE IF NOT EXISTS checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    sprint_id TEXT NOT NULL,
    checkpoint_name TEXT NOT NULL,
    state_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_checkpoints_sprint ON checkpoints(sprint_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_created ON checkpoints(sprint_id, created_at);

CREATE TABLE IF NOT EXISTS agent_health_metrics (
    health_id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_role TEXT NOT NULL,
    project_id TEXT NOT NULL,
    sprint_id TEXT,
    health_score REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'healthy',
    metrics_json TEXT DEFAULT '{}',
    recommendations_json TEXT DEFAULT '[]',
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_agent_health_project ON agent_health_metrics(project_id);
CREATE INDEX IF NOT EXISTS idx_agent_health_sprint ON agent_health_metrics(sprint_id);
CREATE INDEX IF NOT EXISTS idx_agent_health_role ON agent_health_metrics(agent_role);

-- Phase 4 tables
CREATE TABLE IF NOT EXISTS plugins (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    version TEXT NOT NULL,
    type TEXT NOT NULL, -- 'role', 'tool', 'integration'
    metadata TEXT NOT NULL, -- JSON
    config_schema TEXT, -- JSON schema
    installed_at TEXT NOT NULL DEFAULT (datetime('now')),
    enabled INTEGER DEFAULT 1,
    UNIQUE(name, version)
);

CREATE TABLE IF NOT EXISTS team_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    author TEXT NOT NULL,
    version TEXT NOT NULL,
    tags TEXT, -- JSON array
    team_config TEXT NOT NULL, -- JSON
    sprint_config TEXT NOT NULL, -- JSON
    required_plugins TEXT, -- JSON array
    recommended_plugins TEXT, -- JSON array
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    is_public INTEGER DEFAULT 0,
    marketplace_url TEXT,
    downloads INTEGER DEFAULT 0,
    rating REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS teams (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    project_id TEXT NOT NULL,
    agents TEXT NOT NULL, -- JSON array of AgentConfig
    template_id TEXT,
    lead_agent TEXT,
    coordination_channel TEXT,
    sprint_config TEXT NOT NULL, -- JSON
    current_sprint_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES projects (project_id),
    FOREIGN KEY (template_id) REFERENCES team_templates (id)
);

CREATE TABLE IF NOT EXISTS cross_team_dependencies (
    id TEXT PRIMARY KEY,
    dependent_team_id TEXT NOT NULL,
    provider_team_id TEXT NOT NULL,
    dependency_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    due_date TEXT,
    discussion_thread TEXT,
    resolution_notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at TEXT,
    FOREIGN KEY (dependent_team_id) REFERENCES teams (id),
    FOREIGN KEY (provider_team_id) REFERENCES teams (id)
);

CREATE TABLE IF NOT EXISTS integrations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL, -- 'github', 'jira', 'slack'
    project_id TEXT NOT NULL,
    config TEXT NOT NULL, -- JSON configuration
    enabled INTEGER DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES projects (project_id),
    UNIQUE(name, project_id)
);

CREATE TABLE IF NOT EXISTS external_task_mappings (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    external_system TEXT NOT NULL, -- 'jira', 'linear'
    external_task_id TEXT NOT NULL,
    external_url TEXT,
    last_sync TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (task_id) REFERENCES tasks (task_id),
    UNIQUE(task_id, external_system)
);

CREATE TABLE IF NOT EXISTS marketplace_cache (
    id TEXT PRIMARY KEY,
    item_type TEXT NOT NULL, -- 'plugin', 'template'
    item_data TEXT NOT NULL, -- JSON
    cached_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL
);

-- Indexes for Phase 4 tables
CREATE INDEX IF NOT EXISTS idx_plugins_name ON plugins(name);
CREATE INDEX IF NOT EXISTS idx_plugins_type ON plugins(type);
CREATE INDEX IF NOT EXISTS idx_team_templates_author ON team_templates(author);
CREATE INDEX IF NOT EXISTS idx_teams_project ON teams(project_id);
CREATE INDEX IF NOT EXISTS idx_dependencies_dependent ON cross_team_dependencies(dependent_team_id);
CREATE INDEX IF NOT EXISTS idx_dependencies_provider ON cross_team_dependencies(provider_team_id);
CREATE INDEX IF NOT EXISTS idx_integrations_project ON integrations(project_id);
CREATE INDEX IF NOT EXISTS idx_task_mappings_task ON external_task_mappings(task_id);
CREATE INDEX IF NOT EXISTS idx_task_mappings_system ON external_task_mappings(external_system);
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

        # Migration: Add updated_at column to learnings table if it doesn't exist
        try:
            await self._connection.execute(
                "ALTER TABLE learnings ADD COLUMN updated_at TEXT NOT NULL "
                "DEFAULT (datetime('now'))"
            )
        except Exception:
            # Column already exists, ignore
            pass

        # Migration: Add pinned column to learnings table if it doesn't exist
        try:
            await self._connection.execute(
                "ALTER TABLE learnings ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0"
            )
        except Exception:
            # Column already exists, ignore
            pass

        # Migration: Add status column to learnings table if it doesn't exist
        try:
            await self._connection.execute(
                "ALTER TABLE learnings ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'"
            )
        except Exception:
            # Column already exists, ignore
            pass

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
