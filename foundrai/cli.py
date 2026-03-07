"""CLI entry point for FoundrAI."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console

from foundrai.config import FoundrAIConfig, load_config

app = typer.Typer(
    name="foundrai",
    help="FoundrAI — Your AI-Powered Founding Team",
    no_args_is_help=True,
)

# Create sprint subcommand group
sprint_app = typer.Typer(
    name="sprint",
    help="Sprint management commands",
    no_args_is_help=True,
)
app.add_typer(sprint_app, name="sprint")

console = Console()

DEFAULT_YAML_TEMPLATE = '''# FoundrAI Project Configuration
project:
  name: "{name}"
  description: ""

team:
  product_manager:
    enabled: true
    model: anthropic/claude-sonnet-4-20250514
  developer:
    enabled: true
    model: anthropic/claude-sonnet-4-20250514
  qa_engineer:
    enabled: true
    model: anthropic/claude-sonnet-4-20250514

sprint:
  max_tasks_parallel: 3
  token_budget: 100000

persistence:
  database: sqlite
  sqlite_path: .foundrai/data.db

sandbox:
  provider: docker
  timeout_seconds: 30
'''

ENV_EXAMPLE = """# FoundrAI Environment Variables
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
"""

GITIGNORE = """.foundrai/
.env
__pycache__/
*.pyc
.venv/
"""


@app.command()
def init(
    name: str = typer.Argument(..., help="Project name"),
    path: str = typer.Option(".", "--path", help="Directory to create project in"),
) -> None:
    """Initialize a new FoundrAI project."""
    # Basic checks

    # Check Docker availability (warn but don't block)
    try:
        import subprocess
        subprocess.run(["docker", "--version"], capture_output=True, check=True, timeout=5)  # noqa: S607
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        console.print(
            "[yellow]Warning: Docker not available - sandboxed code execution disabled[/yellow]"
        )

    project_dir = Path(path) / name
    project_dir.mkdir(parents=True, exist_ok=True)

    config_path = project_dir / "foundrai.yaml"
    if config_path.exists():
        console.print(f"[yellow]foundrai.yaml already exists in {project_dir}[/yellow]")
    else:
        config_path.write_text(DEFAULT_YAML_TEMPLATE.format(name=name))

    # Create .foundrai structure
    foundrai_dir = project_dir / ".foundrai"
    foundrai_dir.mkdir(exist_ok=True)
    (foundrai_dir / "logs").mkdir(exist_ok=True)
    (foundrai_dir / "artifacts").mkdir(exist_ok=True)

    # Create .env.example
    env_path = project_dir / ".env.example"
    if not env_path.exists():
        env_path.write_text(ENV_EXAMPLE)

    # Create .gitignore
    gitignore_path = project_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text(GITIGNORE)

    console.print(f"[green]✓[/green] Initialized project: {project_dir}")
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print(f"  cd {name}")
    console.print("  export ANTHROPIC_API_KEY=sk-ant-...")
    console.print('  foundrai sprint start "Build a hello world REST API"')


@app.command()
def status(
    project: str = typer.Option(".", "--project", "-p", help="Project directory"),
) -> None:
    """Show current sprint status."""
    project_dir = Path(project)
    if not (project_dir / "foundrai.yaml").exists() and not (project_dir / ".foundrai").exists():
        console.print("[red]Error: Not a FoundrAI project[/red]")
        raise typer.Exit(code=1)

    asyncio.run(_show_status(project_dir))


@app.command()
def logs(
    project: str = typer.Option(".", "--project", "-p", help="Project directory"),
    limit: int = typer.Option(50, "--limit", "-n"),
) -> None:
    """Show agent activity logs."""
    project_dir = Path(project)
    if not (project_dir / "foundrai.yaml").exists() and not (project_dir / ".foundrai").exists():
        console.print("[red]Error: Not a FoundrAI project[/red]")
        raise typer.Exit(code=1)

    asyncio.run(_show_logs(project_dir, limit))


@sprint_app.command("start")
def sprint_start(
    goal: str = typer.Argument(..., help="Sprint goal"),
    project: str = typer.Option(".", "--project", "-p", help="Project directory"),
) -> None:
    """Start a new sprint with the given goal."""
    project_dir = Path(project)
    if not (project_dir / "foundrai.yaml").exists():
        console.print(f"[red]Error: foundrai.yaml not found in {project_dir}[/red]")
        raise typer.Exit(code=1)

    # Check for API keys before starting
    from os import getenv
    has_openai = getenv("OPENAI_API_KEY")
    has_anthropic = getenv("ANTHROPIC_API_KEY")

    if not has_openai and not has_anthropic:
        console.print("[red]Error: No LLM API keys found.[/red]")
        console.print("Set at least one of:")
        console.print("  export OPENAI_API_KEY=sk-...")
        console.print("  export ANTHROPIC_API_KEY=sk-ant-...")
        raise typer.Exit(code=1)

    try:
        asyncio.run(_run_sprint(project_dir, goal))
    except KeyboardInterrupt:
        console.print("\n[yellow]Sprint interrupted by user[/yellow]")
        raise typer.Exit(code=1) from None
    except Exception as e:
        console.print(f"[red]Sprint failed: {e}[/red]")
        raise typer.Exit(code=1) from e


@app.command()
def serve(
    project: str = typer.Option(".", "--project", "-p"),
    port: int = typer.Option(8420, "--port"),
) -> None:
    """Start the web dashboard."""
    import uvicorn

    project_dir = Path(project).resolve()
    config = load_config(str(project_dir))

    from foundrai.api import deps
    from foundrai.api.app import create_app

    deps.set_project_dir(str(project_dir))
    app = create_app(config)
    uvicorn.run(app, host=config.server.host, port=port)


@app.command()
def doctor() -> None:
    """Check system prerequisites and configuration."""
    import subprocess
    import sys
    from os import getenv

    console.print("[bold]🏥 FoundrAI System Health Check[/bold]\n")

    issues = []

    # Python version
    console.print("[green]✓[/green] Python version: " + sys.version.split()[0])

    # Docker
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, check=True, timeout=5)  # noqa: S607
        docker_version = result.stdout.decode().strip()
        console.print(f"[green]✓[/green] Docker: {docker_version}")

        # Check if Docker daemon is running
        try:
            subprocess.run(["docker", "ps"], capture_output=True, check=True, timeout=5)  # noqa: S607
            console.print("[green]✓[/green] Docker daemon: Running")
        except subprocess.CalledProcessError:
            console.print("[yellow]⚠[/yellow] Docker daemon: Not running")
            issues.append("Docker daemon not running")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        console.print("[red]✗[/red] Docker: Not available")
        issues.append("Docker not installed or not in PATH")

    # API Keys
    api_keys = []
    if getenv("OPENAI_API_KEY"):
        console.print("[green]✓[/green] OpenAI API key: Set")
        api_keys.append("OpenAI")
    else:
        console.print("[yellow]⚠[/yellow] OpenAI API key: Not set")

    if getenv("ANTHROPIC_API_KEY"):
        console.print("[green]✓[/green] Anthropic API key: Set")
        api_keys.append("Anthropic")
    else:
        console.print("[yellow]⚠[/yellow] Anthropic API key: Not set")

    if not api_keys:
        issues.append("No LLM API keys configured")

    # Dependencies
    try:
        import fastapi
        console.print(f"[green]✓[/green] FastAPI: {fastapi.__version__}")
    except ImportError:
        console.print("[red]✗[/red] FastAPI: Not installed")
        issues.append("FastAPI not installed")

    try:
        import langgraph
        # Try to get version, fall back to just "installed" if no version attr
        try:
            version = langgraph.__version__
        except AttributeError:
            version = "installed"
        console.print(f"[green]✓[/green] LangGraph: {version}")
    except ImportError:
        console.print("[red]✗[/red] LangGraph: Not installed")
        issues.append("LangGraph not installed")

    # Summary
    console.print()
    if issues:
        console.print("[red]❌ Issues found:[/red]")
        for issue in issues:
            console.print(f"  • {issue}")
        console.print()
        console.print("[bold]To fix:[/bold]")
        if "Python 3.11+" in str(issues):
            console.print("  • Upgrade to Python 3.11 or higher")
        if "Docker" in str(issues):
            console.print("  • Install Docker Desktop or Docker Engine")
        if "API keys" in str(issues):
            console.print(
                "  • Set API keys: export OPENAI_API_KEY=sk-... or ANTHROPIC_API_KEY=sk-ant-..."
            )
        if any("not installed" in issue for issue in issues):
            console.print("  • Run: pip install foundrai")
        raise typer.Exit(code=1)
    else:
        console.print("[green]✅ All systems operational![/green]")
        console.print(
            f"Ready to orchestrate AI teams with {', '.join(api_keys)} "
            f"LLM{'s' if len(api_keys) > 1 else ''}"
        )


async def _show_status(project_dir: Path) -> None:
    """Show sprint status."""
    from foundrai.persistence.database import Database

    db_path = str(project_dir / ".foundrai" / "data.db")
    if not Path(db_path).exists():
        console.print("[yellow]No sprints found[/yellow]")
        return

    db = Database(db_path)
    await db.connect()
    try:

        cursor = await db.conn.execute(
            "SELECT * FROM sprints ORDER BY sprint_number DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        if not row:
            console.print("[yellow]No sprints found[/yellow]")
            return

        console.print(f"Sprint #{row['sprint_number']}: {row['goal']}")
        console.print(f"Status: {row['status']}")
    finally:
        await db.close()


async def _show_logs(project_dir: Path, limit: int) -> None:
    """Show event logs."""
    from foundrai.persistence.database import Database
    from foundrai.persistence.event_log import EventLog

    db_path = str(project_dir / ".foundrai" / "data.db")
    if not Path(db_path).exists():
        console.print("[yellow]No events found[/yellow]")
        return

    db = Database(db_path)
    await db.connect()
    try:
        log = EventLog(db)
        events = await log.query(limit=limit)
        if not events:
            console.print("[yellow]No events found[/yellow]")
            return

        for event in reversed(events):
            console.print(f"[dim]{event['timestamp']}[/dim] {event['event_type']}")
    finally:
        await db.close()


async def _run_sprint(project_dir: Path, goal: str) -> None:
    """Run a sprint."""
    from dotenv import load_dotenv

    load_dotenv(project_dir / ".env")

    config = load_config(str(project_dir))

    from foundrai.agents.context import SprintContext
    from foundrai.agents.llm import LLMClient, LLMConfig
    from foundrai.agents.personas.developer import DeveloperAgent
    from foundrai.agents.personas.product_manager import ProductManagerAgent
    from foundrai.agents.personas.qa_engineer import QAEngineerAgent
    from foundrai.agents.roles import get_role
    from foundrai.agents.runtime import AgentRuntime
    from foundrai.models.enums import AgentRoleName
    from foundrai.orchestration.engine import SprintEngine
    from foundrai.orchestration.message_bus import MessageBus
    from foundrai.orchestration.task_graph import TaskGraph
    from foundrai.persistence.artifact_store import ArtifactStore
    from foundrai.persistence.database import Database
    from foundrai.persistence.event_log import EventLog
    from foundrai.persistence.sprint_store import SprintStore

    db_path = str(project_dir / config.persistence.sqlite_path)
    db = Database(db_path)
    await db.connect()

    try:
        event_log = EventLog(db)
        sprint_store = SprintStore(db)
        artifact_store = ArtifactStore(db)
        message_bus = MessageBus(event_log)
        task_graph = TaskGraph()

        # Ensure project row exists
        project_id = config.project.name
        await _ensure_project(db, project_id, config.project.name)
        await _ensure_agent_configs(db, project_id, config)

        sprint_context = SprintContext(
            project_name=config.project.name,
            project_path=str(project_dir),
            sprint_goal=goal,
            sprint_number=await sprint_store.next_sprint_number(project_id),
        )

        # Create agents
        agents: dict[str, object] = {}

        if config.team.product_manager.enabled:
            pm_llm = LLMClient(LLMConfig(model=config.team.product_manager.model))
            pm_runtime = AgentRuntime(llm_client=pm_llm, event_log=event_log)
            agents[AgentRoleName.PRODUCT_MANAGER.value] = ProductManagerAgent(
                role=get_role(AgentRoleName.PRODUCT_MANAGER),
                model=config.team.product_manager.model,
                tools=[],
                message_bus=message_bus,
                sprint_context=sprint_context,
                runtime=pm_runtime,
            )
            message_bus.register_agent(AgentRoleName.PRODUCT_MANAGER.value)

        if config.team.developer.enabled:
            dev_llm = LLMClient(LLMConfig(model=config.team.developer.model))
            dev_runtime = AgentRuntime(llm_client=dev_llm, event_log=event_log)
            agents[AgentRoleName.DEVELOPER.value] = DeveloperAgent(
                role=get_role(AgentRoleName.DEVELOPER),
                model=config.team.developer.model,
                tools=[],
                message_bus=message_bus,
                sprint_context=sprint_context,
                runtime=dev_runtime,
            )
            message_bus.register_agent(AgentRoleName.DEVELOPER.value)

        if config.team.qa_engineer.enabled:
            qa_llm = LLMClient(LLMConfig(model=config.team.qa_engineer.model))
            qa_runtime = AgentRuntime(llm_client=qa_llm, event_log=event_log)
            agents[AgentRoleName.QA_ENGINEER.value] = QAEngineerAgent(
                role=get_role(AgentRoleName.QA_ENGINEER),
                model=config.team.qa_engineer.model,
                tools=[],
                message_bus=message_bus,
                sprint_context=sprint_context,
                runtime=qa_runtime,
            )
            message_bus.register_agent(AgentRoleName.QA_ENGINEER.value)

        # Live output
        async def on_event(event_type: str, data: dict) -> None:
            if event_type == "sprint.status_changed":
                console.print(f"[bold blue]→ {data.get('status', '')}[/bold blue]")
            elif event_type == "task.status_changed":
                console.print(f"  Task {data.get('task_id', '')[:8]}... → {data.get('status', '')}")

        event_log.register_listener(on_event)

        console.print("\n[bold]🚀 Starting Sprint[/bold]")
        console.print(f"   Goal: {goal}\n")

        engine = SprintEngine(
            config=config,
            agents=agents,
            task_graph=task_graph,
            message_bus=message_bus,
            sprint_store=sprint_store,
            event_log=event_log,
            artifact_store=artifact_store,
        )

        # Add timeout to prevent hanging
        try:
            # 1 hour timeout
            result = await asyncio.wait_for(engine.run_sprint(goal, project_id), timeout=3600)
            _print_summary(result)
        except TimeoutError:
            console.print("[red]Sprint timed out after 1 hour[/red]")
            console.print(
                "This may indicate an issue with LLM connectivity or model responsiveness."
            )
            raise typer.Exit(code=1) from None

    finally:
        await db.close()


async def _ensure_project(db: object, project_id: str, name: str) -> None:
    """Ensure a project row exists in the database."""
    cursor = await db.conn.execute(  # type: ignore[union-attr]
        "SELECT 1 FROM projects WHERE project_id = ?", (project_id,)
    )
    if not await cursor.fetchone():
        await db.conn.execute(  # type: ignore[union-attr]
            "INSERT INTO projects (project_id, name) VALUES (?, ?)",
            (project_id, name),
        )
        await db.conn.commit()  # type: ignore[union-attr]


async def _ensure_agent_configs(db: object, project_id: str, config: FoundrAIConfig) -> None:
    """Populate agent_configs table from config."""
    team_map = {
        "product_manager": config.team.product_manager,
        "developer": config.team.developer,
        "qa_engineer": config.team.qa_engineer,
        "architect": config.team.architect,
        "designer": config.team.designer,
    }
    for role, ac in team_map.items():
        cursor = await db.conn.execute(  # type: ignore[union-attr]
            "SELECT 1 FROM agent_configs WHERE project_id = ? AND agent_role = ?",
            (project_id, role),
        )
        if not await cursor.fetchone():
            await db.conn.execute(  # type: ignore[union-attr]
                "INSERT INTO agent_configs"
                " (project_id, agent_role, autonomy_level, model, enabled)"
                " VALUES (?, ?, ?, ?, ?)",
                (project_id, role, ac.autonomy.value, ac.model, int(ac.enabled)),
            )
    await db.conn.commit()  # type: ignore[union-attr]


def _print_summary(state: dict) -> None:
    """Print sprint summary to console."""
    from foundrai.models.sprint import SprintMetrics

    status = state.get("status", "unknown")
    status_str = status.value if hasattr(status, "value") else str(status)

    metrics = state.get("metrics")
    if isinstance(metrics, SprintMetrics):
        total = metrics.total_tasks
        completed = metrics.completed_tasks
        failed = metrics.failed_tasks
        tokens = metrics.total_tokens
    else:
        total = 0
        completed = 0
        failed = 0
        tokens = 0

    console.print()
    if status_str in ("completed", "COMPLETED"):
        num = state.get('sprint_number', '?')
        console.print(f"[bold green]✅ Sprint #{num} COMPLETED[/bold green]")
    else:
        num = state.get('sprint_number', '?')
        console.print(f"[bold red]❌ Sprint #{num} FAILED[/bold red]")

    console.print(f"  Tasks: {total} total, {completed} passed, {failed} failed")
    console.print(f"  Tokens: {tokens}")

    artifacts = state.get("artifacts", [])
    if artifacts:
        console.print(f"  Artifacts: {len(artifacts)} files")
