"""Team template models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TeamTemplate(BaseModel):
    """Team template model."""

    id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    name: str
    description: str = ""
    author: str
    version: str = "1.0.0"
    tags: list[str] = Field(default_factory=list)

    # Core configuration - stored as dicts to avoid circular imports
    team_config: dict[str, Any]
    sprint_config: dict[str, Any]

    # Plugin requirements
    required_plugins: list[str] = Field(default_factory=list)
    recommended_plugins: list[str] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    downloads: int = 0
    rating: float = 0.0
    rating_count: int = 0

    # Marketplace
    is_public: bool = False
    marketplace_url: str | None = None

    # Repository info
    repository_url: str | None = None
    documentation_url: str | None = None
    license: str = "MIT"


class CreateTemplateRequest(BaseModel):
    """Request model for creating a team template."""

    name: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    is_public: bool = False


class TemplateListing(BaseModel):
    """Template listing from marketplace."""

    id: str
    name: str
    description: str
    author: str
    version: str
    download_count: int = 0
    rating: float = 0.0
    rating_count: int = 0
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    # Rich metadata
    screenshots: list[str] = Field(default_factory=list)
    documentation_url: str | None = None
    repository_url: str | None = None
    license: str = "MIT"

    # Compatibility
    foundrai_version: str = ">=0.4.0"
    required_plugins: list[str] = Field(default_factory=list)


class PublishConfig(BaseModel):
    """Configuration for publishing template to marketplace."""

    is_public: bool = True
    tags: list[str] = Field(default_factory=list)
    description_override: str | None = None
    documentation_url: str | None = None
