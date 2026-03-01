# FoundrAI — Claude Code Context

## Project Overview
FoundrAI is an open-source AI agent orchestration platform that visualizes and manages autonomous AI agents working together as an Agile startup team. Users define a high-level goal, and a team of specialized AI agents (PM, Architect, Developer, QA, Designer, DevOps) self-organizes into sprints to decompose, plan, and execute — while the user watches it all unfold on a live visual dashboard.

**Tagline:** "Your AI-powered founding team"

## Core Differentiators
1. **Live Sprint Dashboard** — Real-time Kanban board + agent activity feed. No other tool offers this.
2. **True Agile Methodology** — Sprint planning, execution, reviews, retrospectives. Agents iterate and improve.
3. **Configurable Autonomy** — Per-agent, per-action-type approval policies. Not a binary switch.
4. **Agent Observability** — Full event log, communication traces, cost tracking, performance analytics.
5. **Model-Agnostic** — Assign different LLMs to different agent roles via LiteLLM.

## Tech Stack
- **Backend:** Python 3.11+, FastAPI, LangGraph, LiteLLM
- **Frontend:** React, TypeScript, Vite, React Flow, Recharts
- **Database:** SQLite (local-first), optional PostgreSQL
- **Vector Store:** ChromaDB (embedded)
- **CLI:** Typer
- **Real-time:** WebSockets (FastAPI native)
- **Sandboxing:** Docker / E2B for code execution
- **Package Management:** uv + Poetry

## Architecture Layers
1. **Agent Layer** — Individual AI agents with roles, personas, tools, memory (LangGraph + LiteLLM)
2. **Orchestration Layer** — Sprint engine, task graph, message bus, human gateway, Agile coordinator
3. **Persistence Layer** — Sprint store, artifact store, event log, vector memory
4. **API Layer** — REST API (FastAPI), WebSocket server, CLI (Typer), Plugin API
5. **Frontend Layer** — Sprint board, agent feed, goal tree, metrics dashboard, control panel

## Code Conventions
- Python: Follow PEP 8, use type hints everywhere, Pydantic for all data models
- Async-first: Use `async/await` for all I/O operations
- Testing: pytest + pytest-asyncio, aim for 80%+ coverage on core orchestration
- Docstrings: Google-style docstrings on all public functions and classes
- Frontend: Functional React components with hooks, TypeScript strict mode
- Naming: snake_case for Python, camelCase for TypeScript, PascalCase for components/classes

## Git Conventions
- Branch naming: `feat/`, `fix/`, `docs/`, `refactor/`
- Commit messages: Conventional Commits (feat:, fix:, docs:, refactor:, test:, chore:)
- PR descriptions: Include what changed, why, and how to test

## Key Design Principles
- **Local-first:** Everything works with SQLite + ChromaDB, zero external dependencies to start
- **Model-agnostic:** Never hard-code a specific LLM provider. Always go through LiteLLM.
- **Plugin-extensible:** Custom agent roles, tools, and integrations via well-defined interfaces
- **Observable by default:** Every agent action, message, and decision is logged and streamable
- **Human-in-the-loop:** Configurable approval gates, never fully black-box

## Agent Roles (Default Team)
| Role | Responsibilities | Default Model |
|------|-----------------|---------------|
| ProductManager | Goal decomposition, backlog prioritization, acceptance criteria | Claude (best at planning/writing) |
| Architect | System design, tech decisions, code review oversight | Claude or GPT-4o |
| Developer | Code implementation from stories, PR submission, bug fixes | GPT-4o or Claude (best at code) |
| QAEngineer | Test case creation, code review, bug reporting | Any capable model |
| Designer | UI/UX mockups, design specs, visual review | Claude or GPT-4o |
| DevOps | CI/CD setup, deployment, monitoring | Any capable model |

## Sprint Lifecycle
1. **Planning** — PM agent decomposes goal → epics → stories → tasks. Human reviews.
2. **Execution** — Agents work on assigned tasks. Parallel where dependencies allow.
3. **Review** — Agents present completed work. Quality assessed. Incomplete tasks → backlog.
4. **Retrospective** — Agents analyze performance, update vector memory with learnings.
5. **Next Sprint** — Improved team starts next sprint with accumulated knowledge.

## File Structure
```
foundrai/
├── foundrai/              # Python backend package
│   ├── agents/            # Agent definitions and runtime
│   ├── orchestration/     # Sprint engine and coordination
│   ├── persistence/       # Storage and memory
│   ├── api/               # FastAPI server and routes
│   ├── tools/             # Agent tools (code exec, file mgmt, etc.)
│   └── plugins/           # Plugin interface
├── frontend/              # React frontend
│   └── src/
│       ├── components/    # UI components
│       ├── hooks/         # WebSocket and state hooks
│       └── stores/        # State management
├── tests/                 # Test suite
├── docs/                  # Documentation
└── docker-compose.yml     # Docker setup
```

## Current Phase
**Phase 0 — Foundation**: Building core agent orchestration engine with basic PM, Developer, QA roles and sequential task execution.

## Commands Reference
- `foundrai init` — Initialize a new project
- `foundrai team create` — Configure agent team
- `foundrai sprint start` — Start a sprint with a goal
- `foundrai status` — Show current sprint status
- `foundrai logs` — Stream agent activity logs
- `foundrai serve` — Start the web dashboard

## Important Notes
- Never store API keys in code. Use environment variables or .env files.
- All agent communication goes through the MessageBus — no direct agent-to-agent calls.
- Every state mutation must emit an event to the EventLog.
- The SprintEngine is the single source of truth for sprint state.
- Frontend connects via WebSocket for real-time updates — never poll.
