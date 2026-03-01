# FoundrAI — Tech Stack Decisions

## Backend

### Python 3.11+
**Why:** Best AI/ML ecosystem by far. LangChain, LangGraph, LiteLLM, ChromaDB are all Python-native. Async support is mature. Largest pool of AI-focused contributors.

### FastAPI
**Why:** Async-native, built-in WebSocket support, auto-generated OpenAPI docs, Pydantic integration for request/response validation. Perfect for real-time AI applications.

### LangGraph
**Why:** State machine model maps perfectly to sprint lifecycle (Planning → Execution → Review → Retro). Built-in checkpointing lets us pause/resume sprints. Conditional edges for dynamic flow control. Human-in-the-loop support is first-class.

**Alternative considered:** Custom orchestration engine. Rejected because LangGraph provides checkpointing, visualization, and debugging tools we'd have to build from scratch.

### LiteLLM
**Why:** Unified API for 100+ LLM providers (OpenAI, Anthropic, Ollama, Together, Groq, etc.). Enables our core feature of assigning different models to different agent roles without any code changes. Also provides cost tracking out of the box.

**Alternative considered:** Direct provider SDKs. Rejected because it would tightly couple agents to specific providers.

### Typer
**Why:** Modern CLI framework built on Click. Auto-generated help text, rich terminal output, type-hint-based argument parsing. Matches FastAPI's developer experience philosophy.

## Data Layer

### SQLite (Primary) → PostgreSQL (Optional)
**Why:** Local-first philosophy. SQLite requires zero configuration — `foundrai init` and you're running. For team deployments or production use, PostgreSQL can be swapped in via configuration.

**Access:** aiosqlite for async operations, maintaining FastAPI's non-blocking architecture.

### ChromaDB
**Why:** Embedded vector database. Zero external dependencies, runs in-process. Perfect for the agent long-term memory system. Supports multiple embedding models.

**Alternative considered:** Pinecone, Weaviate. Rejected because they require external services, violating local-first principle.

## Frontend

### React + TypeScript + Vite
**Why:** Industry standard for complex interactive UIs. TypeScript for type safety. Vite for fast dev server and builds. Largest ecosystem for the visualization libraries we need.

### React Flow
**Why:** Purpose-built for interactive node-based graphs. Perfect for the Goal Decomposition View (goal → epics → stories → tasks) and Agent Communication Graph. Highly customizable.

### Recharts
**Why:** React-native charting library. Clean API, good defaults, responsive. For the Metrics Dashboard (velocity charts, cost breakdowns, agent performance).

### WebSocket Client
**Why:** Native browser WebSocket API + custom React hooks. Enables real-time streaming of agent activity to the Sprint Board and Agent Feed without polling.

## Infrastructure

### Docker
**Why:** Two uses: (1) Containerize FoundrAI itself for easy deployment. (2) Sandboxed code execution — agents run generated code inside isolated Docker containers for safety.

### E2B (Optional)
**Why:** Cloud-based sandboxed environments for code execution. Alternative to local Docker when running in cloud environments or when users don't have Docker installed.

## Package Management

### uv + Poetry
**Why:** uv for fast dependency resolution and virtual environment management. Poetry for pyproject.toml-based package definition and publishing. Both are modern Python standards.

## Testing

### pytest + pytest-asyncio
**Why:** Standard Python testing. pytest-asyncio for testing async FastAPI endpoints and agent execution loops. Property-based testing with Hypothesis for the TaskGraph scheduler.

### Vitest
**Why:** Frontend testing framework. Compatible with Vite, fast execution, good React Testing Library integration.

## CI/CD

### GitHub Actions
**Why:** Free for open source, largest ecosystem of actions, native GitHub integration. Runs: linting (ruff), type checking (mypy), tests (pytest + vitest), build verification.
