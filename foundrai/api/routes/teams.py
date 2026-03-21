"""Multi-team coordination API routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from foundrai.models.team import (
    CreateDependencyRequest,
    CreateTeamRequest,
    CrossTeamDependency,
    Team,
)
from foundrai.persistence.team_store import TeamStore

router = APIRouter()
logger = logging.getLogger(__name__)


def get_team_store() -> TeamStore:
    """Get team store dependency."""
    # In a real implementation, this would come from dependency injection
    from foundrai.persistence.database import Database

    db = Database("temp.db")  # This should be injected
    return TeamStore(db)


@router.get("/projects/{project_id}/teams", response_model=list[Team])
async def list_teams(project_id: str, store: TeamStore = Depends(get_team_store)) -> list[Team]:
    """List teams in project."""
    try:
        teams = await store.list_teams(project_id=project_id)
        return teams

    except Exception as e:
        logger.error(f"Failed to list teams for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list teams") from e


@router.post("/projects/{project_id}/teams", response_model=Team)
async def create_team(
    project_id: str, request: CreateTeamRequest, store: TeamStore = Depends(get_team_store)
) -> Team:
    """Create new team in project."""
    try:
        from foundrai.config import SprintConfig

        # Create basic team configuration
        team = Team(
            name=request.name,
            description=request.description,
            project_id=project_id,
            agents=[],  # Will be populated from template or manual config
            template_id=request.template_id,
            lead_agent=request.lead_agent,
            coordination_channel=request.coordination_channel,
            sprint_config=SprintConfig(),  # Default configuration
        )

        # TODO: If template_id provided, load template and apply configuration
        if request.template_id:
            logger.warning(f"Template application not yet implemented: {request.template_id}")

        created_team = await store.create_team(team)
        return created_team

    except Exception as e:
        logger.error(f"Failed to create team: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create team: {str(e)}") from e


@router.get("/teams/{team_id}", response_model=Team)
async def get_team(team_id: str, store: TeamStore = Depends(get_team_store)) -> Team:
    """Get team details."""
    try:
        team = await store.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        return team

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get team {team_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get team: {str(e)}") from e


@router.put("/teams/{team_id}", response_model=Team)
async def update_team(
    team_id: str, request: CreateTeamRequest, store: TeamStore = Depends(get_team_store)
) -> Team:
    """Update team configuration."""
    try:
        team = await store.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        # Update team fields
        team.name = request.name
        team.description = request.description
        team.template_id = request.template_id
        team.lead_agent = request.lead_agent
        team.coordination_channel = request.coordination_channel

        updated_team = await store.update_team(team)
        return updated_team

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update team {team_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update team: {str(e)}") from e


@router.delete("/teams/{team_id}")
async def delete_team(team_id: str, store: TeamStore = Depends(get_team_store)) -> dict[str, str]:
    """Delete team."""
    try:
        success = await store.delete_team(team_id)
        if not success:
            raise HTTPException(status_code=404, detail="Team not found")

        return {"message": "Team deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete team {team_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete team: {str(e)}") from e


@router.get("/teams/{team_id}/dependencies", response_model=list[CrossTeamDependency])
async def list_dependencies(
    team_id: str, store: TeamStore = Depends(get_team_store)
) -> list[CrossTeamDependency]:
    """List dependencies for team."""
    try:
        dependencies = await store.list_dependencies(team_id=team_id)
        return dependencies

    except Exception as e:
        logger.error(f"Failed to list dependencies for team {team_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list dependencies") from e


@router.post("/teams/{team_id}/dependencies", response_model=CrossTeamDependency)
async def create_dependency(
    team_id: str, request: CreateDependencyRequest, store: TeamStore = Depends(get_team_store)
) -> CrossTeamDependency:
    """Create cross-team dependency."""
    try:
        dependency = CrossTeamDependency(
            dependent_team_id=team_id,
            provider_team_id=request.provider_team_id,
            dependency_type=request.dependency_type,
            title=request.title,
            description=request.description,
            due_date=request.due_date,
            priority=request.priority,
        )

        created_dependency = await store.create_dependency(dependency)
        return created_dependency

    except Exception as e:
        logger.error(f"Failed to create dependency: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create dependency: {str(e)}") from e


@router.get("/dependencies/{dependency_id}", response_model=CrossTeamDependency)
async def get_dependency(
    dependency_id: str, store: TeamStore = Depends(get_team_store)
) -> CrossTeamDependency:
    """Get dependency details."""
    try:
        dependency = await store.get_dependency(dependency_id)
        if not dependency:
            raise HTTPException(status_code=404, detail="Dependency not found")

        return dependency

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dependency {dependency_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dependency: {str(e)}") from e


@router.put("/dependencies/{dependency_id}", response_model=CrossTeamDependency)
async def update_dependency(
    dependency_id: str, request: CreateDependencyRequest, store: TeamStore = Depends(get_team_store)
) -> CrossTeamDependency:
    """Update dependency."""
    try:
        dependency = await store.get_dependency(dependency_id)
        if not dependency:
            raise HTTPException(status_code=404, detail="Dependency not found")

        # Update dependency fields
        dependency.dependency_type = request.dependency_type
        dependency.title = request.title
        dependency.description = request.description
        dependency.due_date = request.due_date
        dependency.priority = request.priority

        updated_dependency = await store.update_dependency(dependency)
        return updated_dependency

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update dependency {dependency_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update dependency: {str(e)}") from e


@router.get("/projects/{project_id}/dependencies", response_model=list[CrossTeamDependency])
async def list_project_dependencies(
    project_id: str, store: TeamStore = Depends(get_team_store)
) -> list[CrossTeamDependency]:
    """List all dependencies in a project."""
    try:
        dependencies = await store.list_dependencies(project_id=project_id)
        return dependencies

    except Exception as e:
        logger.error(f"Failed to list project dependencies {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list project dependencies") from e
