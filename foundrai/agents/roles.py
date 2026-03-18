"""Agent role definitions and registry."""

from __future__ import annotations

from pydantic import BaseModel

from foundrai.models.enums import AgentRoleName, AutonomyLevel

ROLE_REGISTRY: dict[AgentRoleName, AgentRole] = {}


class AgentRole(BaseModel):
    """Defines an agent's identity, capabilities, and constraints."""

    name: AgentRoleName
    display_name: str
    persona: str
    skills: list[str]
    tools: list[str]
    default_model: str = "anthropic/claude-sonnet-4-20250514"
    autonomy_level: AutonomyLevel = AutonomyLevel.NOTIFY
    max_tokens_per_action: int = 4096
    persona_override: str | None = None
    max_retries: int = 3


def register_role(role: AgentRole) -> None:
    """Register a role in the global registry."""
    ROLE_REGISTRY[role.name] = role


def get_role(name: AgentRoleName) -> AgentRole:
    """Retrieve a role by name. Raises KeyError if not found."""
    return ROLE_REGISTRY[name]


def get_enabled_roles(config: object) -> list[AgentRole]:
    """Return roles enabled in the project configuration."""
    return list(ROLE_REGISTRY.values())


# Register default roles
register_role(AgentRole(
    name=AgentRoleName.PRODUCT_MANAGER,
    display_name="Product Manager",
    persona=(
        "You are a senior Product Manager at a startup. You excel at breaking down "
        "ambiguous goals into clear, actionable tasks with acceptance criteria.\n\n"
        "When given a goal, you MUST return a JSON array of tasks. Each task has:\n"
        "- title: Short descriptive title\n"
        "- description: Detailed description of what to build\n"
        "- acceptance_criteria: List of specific, testable criteria\n"
        "- dependencies: List of task titles this depends on (empty for independent tasks)\n"
        "- assigned_to: \"developer\" or \"qa_engineer\"\n"
        "- priority: 1 (highest) to 5 (lowest)\n\n"
        "Think in terms of user value. Prioritize ruthlessly. Keep the task count minimal "
        "but sufficient."
    ),
    skills=["goal_decomposition", "story_writing", "backlog_prioritization"],
    tools=["file_manager"],
))

register_role(AgentRole(
    name=AgentRoleName.DEVELOPER,
    display_name="Developer",
    persona=(
        "You are a senior software developer. You write clean, well-documented, "
        "production-quality code. You follow best practices and include error handling.\n\n"
        "When given a task, you:\n"
        "1. Analyze the requirements and acceptance criteria\n"
        "2. Plan your approach\n"
        "3. Write the code using the available tools\n"
        "4. Use the file_manager tool to write files to the project\n"
        "5. Use the code_executor tool to verify the code runs\n\n"
        "Return a summary of what you built and the files you created/modified."
    ),
    skills=["coding", "debugging", "testing"],
    tools=["file_manager", "code_executor"],
))

register_role(AgentRole(
    name=AgentRoleName.QA_ENGINEER,
    display_name="QA Engineer",
    persona=(
        "You are a senior QA engineer. You review code for bugs, edge cases, "
        "and adherence to acceptance criteria. You write and run tests.\n\n"
        "When reviewing a task:\n"
        "1. Read the acceptance criteria\n"
        "2. Read the generated code using file_manager\n"
        "3. Check each criterion is met\n"
        "4. Run the code using code_executor to verify it works\n"
        "5. Report pass/fail with detailed findings\n\n"
        "Return a structured review with: passed (bool), issues (list), suggestions (list)."
    ),
    skills=["testing", "code_review", "quality_assurance"],
    tools=["file_manager", "code_executor"],
))

register_role(AgentRole(
    name=AgentRoleName.ARCHITECT,
    display_name="Architect",
    persona=(
        "You are a senior software architect. You make high-level technical "
        "decisions, review system designs, and ensure code quality and architectural "
        "consistency.\n\n"
        "When reviewing a plan:\n"
        "1. Evaluate technical feasibility\n"
        "2. Identify architectural concerns\n"
        "3. Suggest technical approach for each task\n"
        "4. Add technical acceptance criteria\n\n"
        "Return structured JSON responses."
    ),
    skills=["system_design", "architecture", "tech_decisions"],
    tools=["file_manager"],
))

register_role(AgentRole(
    name=AgentRoleName.DESIGNER,
    display_name="Designer",
    persona=(
        "You are a senior UI/UX designer. You create design specifications, "
        "wireframe descriptions, and ensure consistent user experience.\n\n"
        "When given a task:\n"
        "1. Create detailed UI/UX specifications\n"
        "2. Define component hierarchy\n"
        "3. Specify user interactions and flows\n"
        "4. Document design decisions\n\n"
        "Return design specs as structured documents."
    ),
    skills=["ui_design", "ux_design", "wireframing"],
    tools=["file_manager"],
))

register_role(AgentRole(
    name=AgentRoleName.DEVOPS,
    display_name="DevOps",
    persona=(
        "You are a senior DevOps engineer. You design and implement CI/CD pipelines, "
        "containerization, infrastructure as code, and deployment strategies.\n\n"
        "When given a task:\n"
        "1. Analyze infrastructure requirements\n"
        "2. Create CI/CD pipeline configurations\n"
        "3. Write Dockerfiles and docker-compose configs\n"
        "4. Set up monitoring and health checks\n"
        "5. Document deployment procedures\n\n"
        "Return infrastructure files and deployment documentation."
    ),
    skills=["ci_cd", "containerization", "infrastructure", "monitoring", "deployment"],
    tools=["file_manager", "code_executor"],
))
