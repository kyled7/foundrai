"""Enums for FoundrAI."""

from enum import Enum


class SprintStatus(str, Enum):
    CREATED = "created"
    PLANNING = "planning"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TaskStatus(str, Enum):
    BACKLOG = "backlog"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    FAILED = "failed"
    BLOCKED = "blocked"


class MessageType(str, Enum):
    TASK_ASSIGNMENT = "task_assignment"
    TASK_RESULT = "task_result"
    CODE_REVIEW = "code_review"
    BUG_REPORT = "bug_report"
    QUESTION = "question"
    DECISION = "decision"
    STATUS_UPDATE = "status_update"
    GOAL_DECOMPOSITION = "goal_decomposition"


class AutonomyLevel(str, Enum):
    AUTO_APPROVE = "auto_approve"
    NOTIFY = "notify"
    REQUIRE_APPROVAL = "require_approval"
    BLOCK = "block"


class AgentRoleName(str, Enum):
    PRODUCT_MANAGER = "product_manager"
    DEVELOPER = "developer"
    QA_ENGINEER = "qa_engineer"
    ARCHITECT = "architect"
    DESIGNER = "designer"
    DEVOPS = "devops"


class ActionType(str, Enum):
    CODE_WRITE = "code_write"
    CODE_EXECUTE = "code_execute"
    FILE_CREATE = "file_create"
    FILE_MODIFY = "file_modify"
    FILE_DELETE = "file_delete"
    GIT_COMMIT = "git_commit"
    GIT_PUSH = "git_push"
    API_CALL = "api_call"
    TOOL_USE = "tool_use"
    TASK_CREATE = "task_create"
    TASK_ASSIGN = "task_assign"
    MESSAGE_SEND = "message_send"
    CODE_REVIEW = "code_review"
    DEPLOYMENT = "deployment"
