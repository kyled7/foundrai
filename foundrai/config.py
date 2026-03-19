"""Configuration loading for FoundrAI."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from foundrai.models.enums import AutonomyLevel


class ProjectConfig(BaseModel):
    name: str = "my-project"
    description: str = ""


class AgentConfig(BaseModel):
    enabled: bool = True
    model: str = "anthropic/claude-sonnet-4-20250514"
    autonomy: AutonomyLevel = AutonomyLevel.NOTIFY
    max_tokens_per_action: int = 4096
    persona_override: str | None = None
    approval_conditions: dict | None = None
    max_retries: int = 3
    approval_timeout_seconds: int | None = None


class TeamConfig(BaseModel):
    product_manager: AgentConfig = Field(
        default_factory=lambda: AgentConfig(model="anthropic/claude-sonnet-4-20250514")
    )
    architect: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            model="anthropic/claude-sonnet-4-20250514", enabled=False
        )
    )
    developer: AgentConfig = Field(
        default_factory=lambda: AgentConfig(model="anthropic/claude-sonnet-4-20250514")
    )
    qa_engineer: AgentConfig = Field(
        default_factory=lambda: AgentConfig(model="anthropic/claude-sonnet-4-20250514")
    )
    designer: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            model="anthropic/claude-sonnet-4-20250514", enabled=False
        )
    )
    devops: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            model="anthropic/claude-sonnet-4-20250514", enabled=False
        )
    )


class SprintConfig(BaseModel):
    max_tasks_parallel: int = 3
    token_budget: int = 100000
    max_sprints: int = 5
    auto_start_next: bool = False
    max_task_retries: int = 3
    task_timeout_seconds: int = 300


class PersistenceConfig(BaseModel):
    database: str = "sqlite"
    sqlite_path: str = ".foundrai/data.db"


class MemoryConfig(BaseModel):
    provider: str = "chromadb"
    chromadb_path: str = ".foundrai/vectors"
    embedding_model: str = "default"


class SandboxConfig(BaseModel):
    provider: str = "docker"
    timeout_seconds: int = 30
    max_memory_mb: int = 512


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8420
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = ".foundrai/logs/foundrai.log"


class BudgetConfigModel(BaseModel):
    sprint_budget_usd: float = 0.0
    agent_budgets: dict[str, float] = Field(default_factory=dict)
    warning_threshold: float = 0.8  # Percentage (0.0-1.0) at which to trigger warnings
    model_tierdown_map: dict[str, str] = Field(default_factory=dict)  # Model -> fallback model


class FoundrAIConfig(BaseModel):
    """Root configuration model parsed from foundrai.yaml."""

    project: ProjectConfig = Field(default_factory=ProjectConfig)
    team: TeamConfig = Field(default_factory=TeamConfig)
    sprint: SprintConfig = Field(default_factory=SprintConfig)
    persistence: PersistenceConfig = Field(default_factory=PersistenceConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    budget: BudgetConfigModel = Field(default_factory=BudgetConfigModel)
    desktop_mode: bool = False


def load_config(project_dir: str = ".") -> FoundrAIConfig:
    """Load configuration from foundrai.yaml in the project directory."""
    config_path = Path(project_dir) / "foundrai.yaml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"foundrai.yaml not found in {project_dir}. "
            "Run `foundrai init <name>` to create a project."
        )

    with open(config_path) as f:
        raw = yaml.safe_load(f)

    return FoundrAIConfig.model_validate(raw or {})
