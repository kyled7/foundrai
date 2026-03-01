# Contributing to FoundrAI

Thank you for your interest in contributing to FoundrAI! This guide will help you get started.

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker
- uv (Python package manager)

### Setup

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/foundrai.git
cd foundrai

# Install Python dependencies
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Install frontend dependencies
cd frontend
npm install
cd ..

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Run tests
pytest
cd frontend && npm test
```

### Running Locally

```bash
# Terminal 1: Backend
foundrai serve --dev

# Terminal 2: Frontend (with hot reload)
cd frontend
npm run dev
```

## Code Style

### Python
- Follow PEP 8
- Use type hints on all function signatures
- Google-style docstrings on all public functions/classes
- Format with `ruff format`
- Lint with `ruff check`
- Type check with `mypy`

### TypeScript / React
- Functional components with hooks only
- TypeScript strict mode
- Format with Prettier
- Lint with ESLint

## Git Workflow

### Branch Naming
- `feat/short-description` — New features
- `fix/short-description` — Bug fixes
- `docs/short-description` — Documentation
- `refactor/short-description` — Code refactoring
- `test/short-description` — Test additions

### Commit Messages
We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add sprint retrospective ceremony
fix: resolve race condition in message bus
docs: update architecture diagram
refactor: extract base agent class
test: add task graph scheduler tests
chore: update dependencies
```

### Pull Requests
1. Fork the repo and create your branch from `main`
2. Write/update tests for your changes
3. Ensure all tests pass (`pytest` and `npm test`)
4. Ensure linting passes (`ruff check` and `npm run lint`)
5. Write a clear PR description explaining what and why
6. Reference any related issues

## Architecture Guidelines

### Key Principles
- **All agent communication goes through MessageBus** — no direct agent-to-agent calls
- **Every state mutation emits an event** to the EventLog
- **SprintEngine is the single source of truth** for sprint state
- **Frontend connects via WebSocket** for real-time updates — never poll
- **LLM calls always go through LiteLLM** — never import provider SDKs directly

### Adding a New Agent Role
1. Create `foundrai/agents/roles/your_role.py`
2. Define the role config in `foundrai/agents/roles/configs/your_role.yaml`
3. Register in `RoleRegistry`
4. Add tests in `tests/agents/test_your_role.py`

### Adding a New Tool
1. Create `foundrai/tools/your_tool.py`
2. Implement the `BaseTool` interface
3. Register in the ToolKit
4. Add to relevant role configs
5. Add tests in `tests/tools/test_your_tool.py`

## Areas Where Help is Needed

Check our [Issues](../../issues) labeled:
- `good first issue` — Great for newcomers
- `help wanted` — We'd love community input
- `design` — UI/UX design contributions
- `documentation` — Docs improvements

## Questions?

Open a [Discussion](../../discussions) or reach out to the maintainers. We're happy to help!
