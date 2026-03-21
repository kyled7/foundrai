"""Integration API routes."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from foundrai.models.integration import (
    GitHubWebhookRequest,
    IntegrationConfig,
    SlackEventRequest,
)
from foundrai.persistence.integration_store import IntegrationStore

router = APIRouter()
logger = logging.getLogger(__name__)


class EnableIntegrationRequest(BaseModel):
    """Request to enable an integration."""

    config: dict[str, Any]


def get_integration_store() -> IntegrationStore:
    """Get integration store dependency."""
    # In a real implementation, this would come from dependency injection
    from foundrai.persistence.database import Database

    db = Database("temp.db")  # This should be injected
    return IntegrationStore(db)


@router.get("/projects/{project_id}/integrations", response_model=list[IntegrationConfig])
async def list_integrations(
    project_id: str, store: IntegrationStore = Depends(get_integration_store)
) -> list[IntegrationConfig]:
    """List configured integrations."""
    try:
        integrations = await store.list_integrations(project_id)
        return integrations

    except Exception as e:
        logger.error(f"Failed to list integrations for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list integrations") from e


@router.post(
    "/projects/{project_id}/integrations/{integration_name}/enable",
    response_model=IntegrationConfig,
)
async def enable_integration(
    project_id: str,
    integration_name: str,
    request: EnableIntegrationRequest,
    store: IntegrationStore = Depends(get_integration_store),
) -> IntegrationConfig:
    """Enable and configure integration."""
    try:
        from foundrai.models.integration import IntegrationStatus

        # Check if integration already exists
        existing = await store.get_integration_by_name(integration_name, project_id)

        if existing:
            # Update existing integration
            existing.config = request.config
            existing.enabled = True
            existing.status = IntegrationStatus.ENABLED

            updated_integration = await store.update_integration(existing)
            return updated_integration
        else:
            # Create new integration
            integration = IntegrationConfig(
                name=integration_name,
                project_id=project_id,
                integration_type=_get_integration_type(integration_name),
                config=request.config,
                enabled=True,
                status=IntegrationStatus.ENABLED,
            )

            created_integration = await store.create_integration(integration)
            return created_integration

    except Exception as e:
        logger.error(f"Failed to enable integration {integration_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to enable integration: {str(e)}"
        ) from e


@router.post("/projects/{project_id}/integrations/{integration_name}/disable")
async def disable_integration(
    project_id: str, integration_name: str, store: IntegrationStore = Depends(get_integration_store)
) -> dict[str, str]:
    """Disable integration."""
    try:
        integration = await store.get_integration_by_name(integration_name, project_id)
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")

        integration.enabled = False
        await store.update_integration(integration)

        return {"message": f"Integration '{integration_name}' disabled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disable integration {integration_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to disable integration: {str(e)}"
        ) from e


@router.get("/integrations/{integration_name}/config-schema")
async def get_integration_config_schema(integration_name: str) -> dict[str, Any]:
    """Get configuration schema for an integration."""
    try:
        schema = _get_config_schema(integration_name)
        return schema

    except Exception as e:
        logger.error(f"Failed to get config schema for {integration_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get config schema: {str(e)}") from e


@router.post("/integrations/github/webhook")
async def github_webhook(
    request: GitHubWebhookRequest,
    # TODO: Add webhook signature verification
) -> dict[str, str]:
    """Handle GitHub webhook events."""
    try:
        logger.info(f"Received GitHub webhook: {request.event}/{request.action}")

        # TODO: Implement webhook handling based on event type
        if request.event == "pull_request":
            await _handle_github_pull_request(request)
        elif request.event == "issues":
            await _handle_github_issue(request)

        return {"status": "processed"}

    except Exception as e:
        logger.error(f"Failed to process GitHub webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process webhook: {str(e)}") from e


@router.post("/integrations/slack/events")
async def slack_events(
    request: SlackEventRequest,
    # TODO: Add Slack signature verification
) -> dict[str, str]:
    """Handle Slack events and interactions."""
    try:
        # Handle URL verification challenge
        if request.type == "url_verification":
            return {"challenge": request.challenge}

        logger.info(f"Received Slack event: {request.type}")

        # TODO: Implement Slack event handling
        if request.event:
            await _handle_slack_event(request.event)

        return {"status": "processed"}

    except Exception as e:
        logger.error(f"Failed to process Slack event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process event: {str(e)}") from e


def _get_integration_type(integration_name: str) -> str | None:
    """Get integration type based on name."""
    from foundrai.models.integration import IntegrationType

    mapping = {
        "github": IntegrationType.SOURCE_CONTROL,
        "jira": IntegrationType.PROJECT_MANAGEMENT,
        "linear": IntegrationType.PROJECT_MANAGEMENT,
        "slack": IntegrationType.COMMUNICATION,
    }

    return mapping.get(integration_name, IntegrationType.SOURCE_CONTROL)


def _get_config_schema(integration_name: str) -> dict[str, Any]:
    """Get configuration schema for an integration."""
    schemas = {
        "github": {
            "type": "object",
            "properties": {
                "token": {"type": "string", "description": "GitHub personal access token"},
                "organization": {"type": "string", "description": "GitHub organization (optional)"},
                "auto_create_repos": {"type": "boolean", "default": True},
                "auto_create_prs": {"type": "boolean", "default": True},
                "pr_template": {"type": "string", "description": "PR description template"},
            },
            "required": ["token"],
        },
        "slack": {
            "type": "object",
            "properties": {
                "bot_token": {"type": "string", "description": "Slack bot token"},
                "signing_secret": {"type": "string", "description": "Slack signing secret"},
                "channels": {
                    "type": "object",
                    "properties": {
                        "sprint_updates": {"type": "string", "default": "#foundrai-sprints"},
                        "approvals": {"type": "string", "default": "#foundrai-approvals"},
                    },
                },
            },
            "required": ["bot_token", "signing_secret"],
        },
        "jira": {
            "type": "object",
            "properties": {
                "server": {"type": "string", "description": "Jira server URL"},
                "email": {"type": "string", "description": "User email"},
                "token": {"type": "string", "description": "API token"},
                "project_key": {"type": "string", "description": "Jira project key"},
            },
            "required": ["server", "email", "token", "project_key"],
        },
    }

    return schemas.get(integration_name, {})


async def _handle_github_pull_request(request: GitHubWebhookRequest) -> None:
    """Handle GitHub pull request events."""
    logger.info(f"Handling GitHub PR {request.action}")
    # TODO: Implement PR event handling


async def _handle_github_issue(request: GitHubWebhookRequest) -> None:
    """Handle GitHub issue events."""
    logger.info(f"Handling GitHub issue {request.action}")
    # TODO: Implement issue event handling


async def _handle_slack_event(event: dict[str, Any]) -> None:
    """Handle Slack event."""
    event_type = event.get("type", "unknown")
    logger.info(f"Handling Slack event: {event_type}")
    # TODO: Implement Slack event handling
