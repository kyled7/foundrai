"""Autonomy configuration models for granular per-agent per-action control."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from foundrai.models.enums import ActionType, AgentRoleName, AutonomyLevel


class TrustScore(BaseModel):
    """Progressive trust score for an agent-action combination."""

    agent_role: AgentRoleName
    action_type: ActionType
    success_count: int = 0
    total_count: int = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    @property
    def success_rate(self) -> float:
        """Calculate success rate as a percentage (0.0 to 1.0)."""
        if self.total_count == 0:
            return 0.0
        return self.success_count / self.total_count

    @property
    def recommendation(self) -> str | None:
        """Suggest autonomy upgrade if success rate is high enough."""
        if self.total_count < 5:
            # Not enough data to make a recommendation
            return None
        if self.success_rate >= 0.9:
            return "Consider upgrading to AUTO_APPROVE"
        elif self.success_rate < 0.5 and self.total_count >= 10:
            return "Consider downgrading autonomy or reviewing agent"
        return None


class AutonomyMatrix(BaseModel):
    """Matrix of autonomy policies for agent-action combinations.

    Stores mappings of agent_role -> action_type -> autonomy_level.
    """

    project_id: str
    matrix: dict[AgentRoleName, dict[ActionType, AutonomyLevel]] = Field(
        default_factory=dict
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def get_autonomy_level(
        self, agent_role: AgentRoleName, action_type: ActionType
    ) -> AutonomyLevel:
        """Get autonomy level for a specific agent-action combination.

        Returns REQUIRE_APPROVAL if not explicitly configured.
        """
        return self.matrix.get(agent_role, {}).get(
            action_type, AutonomyLevel.REQUIRE_APPROVAL
        )

    def set_autonomy_level(
        self,
        agent_role: AgentRoleName,
        action_type: ActionType,
        autonomy_level: AutonomyLevel,
    ) -> None:
        """Set autonomy level for a specific agent-action combination."""
        if agent_role not in self.matrix:
            self.matrix[agent_role] = {}
        self.matrix[agent_role][action_type] = autonomy_level
        self.updated_at = datetime.utcnow()


class AutonomyProfile(BaseModel):
    """Preset autonomy configuration profile.

    Profiles include: Full Autonomy, Supervised, Manual Review, Custom.
    """

    profile_id: str
    name: str
    description: str
    matrix: dict[AgentRoleName, dict[ActionType, AutonomyLevel]] = Field(
        default_factory=dict
    )
    is_builtin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @staticmethod
    def get_full_autonomy_profile() -> AutonomyProfile:
        """Create Full Autonomy profile - all actions auto-approved."""
        matrix: dict[AgentRoleName, dict[ActionType, AutonomyLevel]] = {}
        for role in AgentRoleName:
            matrix[role] = {
                action: AutonomyLevel.AUTO_APPROVE for action in ActionType
            }
        return AutonomyProfile(
            profile_id="full-autonomy",
            name="Full Autonomy",
            description="All actions are auto-approved. Use with caution.",
            matrix=matrix,
            is_builtin=True,
        )

    @staticmethod
    def get_supervised_profile() -> AutonomyProfile:
        """Create Supervised profile - safe actions auto-approved, critical require approval."""
        matrix: dict[AgentRoleName, dict[ActionType, AutonomyLevel]] = {}

        # Safe actions that can be auto-approved
        safe_actions = {
            ActionType.CODE_REVIEW,
            ActionType.MESSAGE_SEND,
            ActionType.TASK_CREATE,
            ActionType.TASK_ASSIGN,
        }

        # Critical actions that require approval
        critical_actions = {
            ActionType.GIT_PUSH,
            ActionType.DEPLOYMENT,
            ActionType.FILE_DELETE,
            ActionType.CODE_EXECUTE,
        }

        for role in AgentRoleName:
            matrix[role] = {}
            for action in ActionType:
                if action in safe_actions:
                    matrix[role][action] = AutonomyLevel.AUTO_APPROVE
                elif action in critical_actions:
                    matrix[role][action] = AutonomyLevel.REQUIRE_APPROVAL
                else:
                    # Default to notify for other actions
                    matrix[role][action] = AutonomyLevel.NOTIFY

        return AutonomyProfile(
            profile_id="supervised",
            name="Supervised",
            description="Safe actions auto-approved, critical actions require approval.",
            matrix=matrix,
            is_builtin=True,
        )

    @staticmethod
    def get_manual_review_profile() -> AutonomyProfile:
        """Create Manual Review profile - all actions require approval."""
        matrix: dict[AgentRoleName, dict[ActionType, AutonomyLevel]] = {}

        # Only read-only/observational actions can be auto-approved
        safe_readonly_actions = {
            ActionType.CODE_REVIEW,
            ActionType.MESSAGE_SEND,
        }

        for role in AgentRoleName:
            matrix[role] = {}
            for action in ActionType:
                if action in safe_readonly_actions:
                    matrix[role][action] = AutonomyLevel.NOTIFY
                else:
                    matrix[role][action] = AutonomyLevel.REQUIRE_APPROVAL

        return AutonomyProfile(
            profile_id="manual-review",
            name="Manual Review",
            description="All significant actions require approval.",
            matrix=matrix,
            is_builtin=True,
        )
