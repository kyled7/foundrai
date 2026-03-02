# FoundrAI — Phase 3 Technical Design Document

> **Status:** Draft  
> **Version:** 1.0  
> **Date:** 2026-03-02  
> **Scope:** Observability — Analytics, cost tracking, decision tracing, and diagnostics  
> **Depends on:** Phase 0 (Foundation) ✅, Phase 1 (Visual Layer) ✅, Phase 2 (Agile Engine) ✅

---

## Table of Contents

1. [Scope & Goals](#1-scope--goals)
2. [Token Cost Tracking](#2-token-cost-tracking)
3. [Token Budget System](#3-token-budget-system)
4. [Analytics Dashboard](#4-analytics-dashboard)
5. [Decision Trace Viewer](#5-decision-trace-viewer)
6. [Communication Graph](#6-communication-graph)
7. [Sprint Comparison View](#7-sprint-comparison-view)
8. [Error Diagnosis Tools](#8-error-diagnosis-tools)
9. [Event Replay System](#9-event-replay-system)
10. [Database Schema Changes](#10-database-schema-changes)
11. [API Changes](#11-api-changes)
12. [Frontend Changes](#12-frontend-changes)
13. [Testing Strategy](#13-testing-strategy)

---

## 1. Scope & Goals

### What Phase 3 Delivers

Phase 3 adds full **observability** to FoundrAI — transforming it from "run sprints and see results" into "understand exactly what happened, why, and at what cost." Think Datadog for your AI team.

### Deliverables

| Deliverable | Description |
|---|---|
| Token cost tracking | Per-agent, per-task, per-sprint token usage and USD cost |
| Token budget system | Set spending limits per sprint/agent with enforcement |
| Analytics dashboard | Visual metrics for performance, quality, and cost |
| Decision trace viewer | Expand any agent decision to see full reasoning chain |
| Communication graph | Visualize agent-to-agent message flow |
| Sprint comparison view | Compare velocity, quality, cost across sprints |
| Error diagnosis tools | Structured error capture with context and suggested fixes |
| Event replay system | Replay any sprint from its event log with playback controls |

### Definition of Done

A user can fully understand why agents made every decision, track costs precisely, and diagnose any failures — like having Datadog for their AI team.

---

## 2. Token Cost Tracking

### 2.1 Design Overview

LiteLLM already returns token usage stats (`prompt_tokens`, `completion_tokens`, `total_tokens`) on every completion response. Phase 3 captures these at the `AgentRuntime` level after each LLM call and persists them to a new `token_usage` table.

### 2.2 Token Usage Model

```python
# foundrai/models/token_usage.py

from pydantic import BaseModel, Field
from datetime import datetime, UTC


class TokenUsage(BaseModel):
    """Single LLM call token usage record."""
    id: str = Field(default_factory=generate_id)
    task_id: str | None = None
    sprint_id: str
    project_id: str
    agent_role: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class TokenUsageSummary(BaseModel):
    """Aggregated token usage for API responses."""
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    call_count: int = 0
    by_agent: dict[str, "TokenUsageSummary"] = {}
    by_model: dict[str, "TokenUsageSummary"] = {}
```

### 2.3 Cost Calculation

Use LiteLLM's built-in cost tracking via `litellm.completion_cost()`, with a fallback lookup table for custom/local models:

```python
# foundrai/agents/cost_tracker.py

import litellm


# Fallback pricing per 1K tokens (input, output) in USD
FALLBACK_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o": (0.0025, 0.01),
    "gpt-4o-mini": (0.00015, 0.0006),
    "claude-sonnet-4-20250514": (0.003, 0.015),
    "claude-haiku-4-20250414": (0.0008, 0.004),
    "deepseek-chat": (0.00014, 0.00028),
}


def calculate_cost(
    model: str, prompt_tokens: int, completion_tokens: int,
    response: object | None = None,
) -> float:
    """Calculate USD cost for an LLM call."""
    # Try LiteLLM's built-in cost calculation first
    if response is not None:
        try:
            return litellm.completion_cost(completion_response=response)
        except Exception:
            pass

    # Fallback to lookup table
    pricing = FALLBACK_PRICING.get(model)
    if pricing:
        input_price, output_price = pricing
        return (prompt_tokens / 1000 * input_price) + (completion_tokens / 1000 * output_price)

    # Unknown model — estimate conservatively
    return (prompt_tokens + completion_tokens) / 1000 * 0.002
```

### 2.4 Capturing Usage in AgentRuntime

Hook into the existing `AgentRuntime.call_llm()` method to record usage after every call:

```python
# foundrai/agents/runtime.py (modified)

class AgentRuntime:
    def __init__(self, ..., token_store: TokenStore | None = None):
        self._token_store = token_store

    async def call_llm(self, messages: list[dict], **kwargs) -> LLMResponse:
        """Call LLM and record token usage."""
        response = await self._llm_client.complete(messages, **kwargs)

        # Record token usage
        if self._token_store and response.usage:
            usage = TokenUsage(
                task_id=self._current_task_id,
                sprint_id=self._current_sprint_id,
                project_id=self._current_project_id,
                agent_role=self.role,
                model=response.model,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                cost_usd=calculate_cost(
                    response.model,
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                    response=response.raw,
                ),
            )
            await self._token_store.record(usage)

        return response
```

### 2.5 Token Store

```python
# foundrai/persistence/token_store.py

class TokenStore:
    """Persistence layer for token usage records."""

    def __init__(self, db: Database) -> None:
        self._db = db

    async def record(self, usage: TokenUsage) -> None:
        """Insert a single usage record."""
        await self._db.execute(
            """INSERT INTO token_usage 
               (id, task_id, sprint_id, project_id, agent_role, model,
                prompt_tokens, completion_tokens, total_tokens, cost_usd, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (usage.id, usage.task_id, usage.sprint_id, usage.project_id,
             usage.agent_role, usage.model, usage.prompt_tokens,
             usage.completion_tokens, usage.total_tokens, usage.cost_usd,
             usage.timestamp),
        )

    async def get_sprint_summary(self, sprint_id: str) -> TokenUsageSummary:
        """Aggregate usage for a sprint."""
        rows = await self._db.fetch_all(
            "SELECT * FROM token_usage WHERE sprint_id = ?", (sprint_id,),
        )
        return self._aggregate(rows)

    async def get_agent_summary(
        self, sprint_id: str, agent_role: str
    ) -> TokenUsageSummary:
        """Aggregate usage for a specific agent in a sprint."""
        rows = await self._db.fetch_all(
            "SELECT * FROM token_usage WHERE sprint_id = ? AND agent_role = ?",
            (sprint_id, agent_role),
        )
        return self._aggregate(rows)

    async def get_project_summary(self, project_id: str) -> TokenUsageSummary:
        """Aggregate usage across all sprints in a project."""
        rows = await self._db.fetch_all(
            "SELECT * FROM token_usage WHERE project_id = ?", (project_id,),
        )
        return self._aggregate(rows)

    async def get_task_usage(self, task_id: str) -> list[TokenUsage]:
        """Get all usage records for a specific task."""
        rows = await self._db.fetch_all(
            "SELECT * FROM token_usage WHERE task_id = ?", (task_id,),
        )
        return [TokenUsage(**row) for row in rows]

    def _aggregate(self, rows: list[dict]) -> TokenUsageSummary:
        summary = TokenUsageSummary()
        by_agent: dict[str, list] = {}
        by_model: dict[str, list] = {}

        for row in rows:
            summary.total_prompt_tokens += row["prompt_tokens"]
            summary.total_completion_tokens += row["completion_tokens"]
            summary.total_tokens += row["total_tokens"]
            summary.total_cost_usd += row["cost_usd"]
            summary.call_count += 1
            by_agent.setdefault(row["agent_role"], []).append(row)
            by_model.setdefault(row["model"], []).append(row)

        summary.by_agent = {k: self._aggregate(v) for k, v in by_agent.items()}
        summary.by_model = {k: self._aggregate(v) for k, v in by_model.items()}
        return summary
```

---

## 3. Token Budget System

### 3.1 Design Overview

Budgets can be configured per-sprint and per-agent-role, with enforcement at the `AgentRuntime` level before each LLM call. Budgets are defined in `foundrai.yaml` and can be overridden via API at runtime.

### 3.2 Budget Configuration

```yaml
# foundrai.yaml
budgets:
  default_sprint_budget_usd: 5.00
  default_agent_budgets_usd:
    product_manager: 1.00
    developer: 2.00
    qa_engineer: 1.00
    architect: 0.50
    designer: 0.50
  warning_threshold: 0.80   # Emit warning at 80%
  hard_limit: true           # Stop at 100% (vs. warn-only)
```

### 3.3 Budget Model

```python
# foundrai/models/budget.py

class BudgetConfig(BaseModel):
    """Budget configuration for a sprint or agent."""
    budget_usd: float
    warning_threshold: float = 0.80
    hard_limit: bool = True


class BudgetStatus(BaseModel):
    """Current budget status."""
    budget_usd: float
    spent_usd: float
    remaining_usd: float
    utilization: float  # 0.0 - 1.0+
    status: str  # "ok" | "warning" | "exceeded"

    @classmethod
    def from_budget(cls, budget_usd: float, spent_usd: float, 
                    warning_threshold: float = 0.80) -> "BudgetStatus":
        remaining = max(0.0, budget_usd - spent_usd)
        utilization = spent_usd / budget_usd if budget_usd > 0 else 0.0
        if utilization >= 1.0:
            status = "exceeded"
        elif utilization >= warning_threshold:
            status = "warning"
        else:
            status = "ok"
        return cls(
            budget_usd=budget_usd,
            spent_usd=round(spent_usd, 6),
            remaining_usd=round(remaining, 6),
            utilization=round(utilization, 4),
            status=status,
        )
```

### 3.4 Budget Enforcement in AgentRuntime

```python
# foundrai/agents/runtime.py (modified)

class BudgetExceededError(Exception):
    """Raised when an agent's token budget is exhausted."""
    def __init__(self, agent_role: str, budget_usd: float, spent_usd: float):
        self.agent_role = agent_role
        self.budget_usd = budget_usd
        self.spent_usd = spent_usd
        super().__init__(
            f"Budget exceeded for {agent_role}: "
            f"${spent_usd:.4f} / ${budget_usd:.4f}"
        )


class AgentRuntime:
    async def call_llm(self, messages: list[dict], **kwargs) -> LLMResponse:
        """Call LLM with budget enforcement."""
        # --- Budget check BEFORE call ---
        if self._budget_config and self._budget_config.hard_limit:
            status = await self._get_budget_status()
            if status.status == "exceeded":
                raise BudgetExceededError(
                    self.role, status.budget_usd, status.spent_usd
                )
            if status.status == "warning":
                await self._emit_budget_warning(status)

        # --- Make the LLM call ---
        response = await self._llm_client.complete(messages, **kwargs)

        # --- Record usage (from §2.4) ---
        if self._token_store and response.usage:
            usage = self._build_token_usage(response)
            await self._token_store.record(usage)

            # --- Post-call budget check ---
            status = await self._get_budget_status()
            if status.status == "warning":
                await self._emit_budget_warning(status)

        return response

    async def _get_budget_status(self) -> BudgetStatus:
        """Get current budget status for this agent in this sprint."""
        summary = await self._token_store.get_agent_summary(
            self._current_sprint_id, self.role
        )
        return BudgetStatus.from_budget(
            self._budget_config.budget_usd,
            summary.total_cost_usd,
            self._budget_config.warning_threshold,
        )

    async def _emit_budget_warning(self, status: BudgetStatus) -> None:
        """Emit a budget warning event."""
        await self._event_log.append(Event(
            type="budget_warning",
            sprint_id=self._current_sprint_id,
            agent_role=self.role,
            data={
                "budget_usd": status.budget_usd,
                "spent_usd": status.spent_usd,
                "utilization": status.utilization,
            },
        ))
```

### 3.5 Sprint-Level Budget Enforcement

The `SprintEngine` also enforces the overall sprint budget. If the total sprint spend exceeds the sprint budget, all remaining tasks are skipped:

```python
# foundrai/orchestration/engine.py (modified)

async def _execute_node(self, state: SprintState) -> SprintState:
    """Execute tasks with sprint-level budget check."""
    sprint_budget = self._get_sprint_budget(state)

    while True:
        # Check sprint budget
        if sprint_budget:
            sprint_summary = await self._token_store.get_sprint_summary(
                state["sprint_id"]
            )
            sprint_status = BudgetStatus.from_budget(
                sprint_budget, sprint_summary.total_cost_usd
            )
            if sprint_status.status == "exceeded":
                # Mark remaining tasks as skipped
                for task in self.task_graph.get_ready_tasks():
                    task.status = TaskStatus.SKIPPED
                    task.skip_reason = "Sprint budget exceeded"
                break

        ready = self.task_graph.get_ready_tasks()
        if not ready:
            break
        # ... existing parallel execution ...
```

### 3.6 Budget API Override

Budgets from `foundrai.yaml` are defaults. The API allows runtime override:

```
PUT /api/sprints/{sprint_id}/budget
PUT /api/sprints/{sprint_id}/agents/{role}/budget
```

Override values are stored in a `budget_overrides` table and take precedence over config defaults.

---

## 4. Analytics Dashboard

### 4.1 Design Overview

A new **Analytics** page in the frontend providing charts and tables for sprint metrics, agent performance, and cost breakdowns. Built with Recharts (already in the project).

### 4.2 Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  📊 Analytics                          [Sprint ▾] [Range ▾] │
├────────────────┬────────────────┬───────────────┬───────────┤
│  Completion    │  Quality       │  Total Cost   │ Duration  │
│  ██████ 85%    │  ████ 4.2/5    │  $3.42        │ 12m 34s   │
├────────────────┴────────────────┴───────────────┴───────────┤
│                                                             │
│  Cost by Agent (Pie)          │  Cost by Sprint (Bar)       │
│  ┌─────────┐                  │  ┌─┐ ┌─┐ ┌─┐ ┌─┐          │
│  │ PM: 22% │                  │  │ │ │ │ │ │ │ │          │
│  │ Dev: 45%│                  │  └─┘ └─┘ └─┘ └─┘          │
│  │ QA: 18% │                  │  S1   S2   S3   S4          │
│  └─────────┘                  │                             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Agent Performance Table                                    │
│  ┌──────────┬───────┬──────┬──────────┬─────────┐          │
│  │ Agent    │ Tasks │ Pass │ Avg Tok  │ Quality │          │
│  │ PM       │ 12    │ 100% │ 1,240    │ 4.5     │          │
│  │ Developer│ 28    │ 82%  │ 3,420    │ 3.8     │          │
│  │ QA       │ 20    │ 95%  │ 1,100    │ 4.2     │          │
│  └──────────┴───────┴──────┴──────────┴─────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Frontend Components

```typescript
// frontend/src/pages/AnalyticsPage.tsx

interface SprintMetrics {
  sprintId: string;
  sprintNumber: number;
  completionRate: number;
  qualityScore: number;
  totalCostUsd: number;
  durationSeconds: number;
  taskCount: number;
  passRate: number;
}

interface AgentMetrics {
  agentRole: string;
  tasksCompleted: number;
  tasksFailed: number;
  passRate: number;
  avgTokensPerTask: number;
  avgQualityScore: number;
  totalCostUsd: number;
}

const AnalyticsPage: React.FC = () => {
  const [sprintId, setSprintId] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<SprintMetrics | null>(null);
  const [agentMetrics, setAgentMetrics] = useState<AgentMetrics[]>([]);
  const [costByAgent, setCostByAgent] = useState<PieDataPoint[]>([]);
  const [costBySprint, setCostBySprint] = useState<BarDataPoint[]>([]);

  return (
    <div className="analytics-page">
      <header>
        <h1>📊 Analytics</h1>
        <SprintSelector value={sprintId} onChange={setSprintId} />
      </header>

      {/* Summary cards */}
      <MetricCards metrics={metrics} />

      {/* Charts row */}
      <div className="charts-row">
        <CostByAgentPie data={costByAgent} />
        <CostBySprintBar data={costBySprint} />
      </div>

      {/* Agent performance table */}
      <AgentPerformanceTable data={agentMetrics} />
    </div>
  );
};
```

### 4.4 Budget Meter Component

A reusable gauge component displayed on the sprint page and analytics dashboard:

```typescript
// frontend/src/components/analytics/BudgetMeter.tsx

interface BudgetMeterProps {
  label: string;
  budgetUsd: number;
  spentUsd: number;
  warningThreshold?: number; // default 0.8
}

const BudgetMeter: React.FC<BudgetMeterProps> = ({
  label, budgetUsd, spentUsd, warningThreshold = 0.8,
}) => {
  const utilization = budgetUsd > 0 ? spentUsd / budgetUsd : 0;
  const status =
    utilization >= 1.0 ? "exceeded" :
    utilization >= warningThreshold ? "warning" : "ok";

  const colorMap = { ok: "#22c55e", warning: "#f59e0b", exceeded: "#ef4444" };

  return (
    <div className="budget-meter">
      <div className="budget-label">{label}</div>
      <div className="budget-bar">
        <div
          className={`budget-fill budget-${status}`}
          style={{
            width: `${Math.min(utilization * 100, 100)}%`,
            backgroundColor: colorMap[status],
          }}
        />
      </div>
      <div className="budget-text">
        ${spentUsd.toFixed(2)} / ${budgetUsd.toFixed(2)}
      </div>
    </div>
  );
};
```

---

## 5. Decision Trace Viewer

### 5.1 Design Overview

Every LLM call is stored as a **decision trace** — the full prompt, response, tool calls, and reasoning chain. Users can click any event in the activity feed to expand and inspect the full decision.

### 5.2 Decision Trace Model

```python
# foundrai/models/decision_trace.py

class ToolCall(BaseModel):
    """A single tool call within a decision."""
    tool_name: str
    arguments: dict
    result: str | None = None


class DecisionTrace(BaseModel):
    """Full trace of a single agent decision (one LLM call)."""
    id: str = Field(default_factory=generate_id)
    event_id: str | None = None
    task_id: str | None = None
    sprint_id: str
    project_id: str
    agent_role: str
    model: str

    # The LLM interaction
    prompt_messages: list[dict]      # Full message array sent to LLM
    response_text: str               # Final text output
    thinking: str | None = None      # Chain-of-thought / reasoning (if model supports)
    tool_calls: list[ToolCall] = []  # Tool calls made during this decision

    # Metadata
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    duration_ms: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
```

### 5.3 Storage Strategy

Decision traces are large (full prompts + responses). Storage strategy:

1. **Compressed storage**: Prompt/response stored as zlib-compressed TEXT in SQLite
2. **Retention policy**: Keep full traces for last N sprints (configurable, default 10); older sprints keep summary only
3. **Lazy loading**: Frontend fetches trace details on-demand (not in list queries)

```python
# foundrai/persistence/trace_store.py

import zlib
import json


class TraceStore:
    """Persistence layer for decision traces."""

    def __init__(self, db: Database) -> None:
        self._db = db

    async def record(self, trace: DecisionTrace) -> None:
        """Store a decision trace with compressed prompt/response."""
        prompt_compressed = zlib.compress(
            json.dumps(trace.prompt_messages).encode()
        )
        response_compressed = zlib.compress(trace.response_text.encode())
        thinking_compressed = (
            zlib.compress(trace.thinking.encode()) if trace.thinking else None
        )
        tool_calls_json = json.dumps(
            [tc.model_dump() for tc in trace.tool_calls]
        )

        await self._db.execute(
            """INSERT INTO decision_traces
               (id, event_id, task_id, sprint_id, project_id, agent_role, model,
                prompt_compressed, response_compressed, thinking_compressed,
                tool_calls_json, prompt_tokens, completion_tokens, cost_usd,
                duration_ms, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (trace.id, trace.event_id, trace.task_id, trace.sprint_id,
             trace.project_id, trace.agent_role, trace.model,
             prompt_compressed, response_compressed, thinking_compressed,
             tool_calls_json, trace.prompt_tokens, trace.completion_tokens,
             trace.cost_usd, trace.duration_ms, trace.timestamp),
        )

    async def get_trace(self, trace_id: str) -> DecisionTrace | None:
        """Fetch and decompress a single trace."""
        row = await self._db.fetch_one(
            "SELECT * FROM decision_traces WHERE id = ?", (trace_id,),
        )
        if not row:
            return None
        return self._decompress_row(row)

    async def list_by_event(self, event_id: str) -> list[dict]:
        """List trace summaries for an event (without full prompt/response)."""
        rows = await self._db.fetch_all(
            """SELECT id, agent_role, model, prompt_tokens, completion_tokens,
                      cost_usd, duration_ms, timestamp
               FROM decision_traces WHERE event_id = ?
               ORDER BY timestamp""",
            (event_id,),
        )
        return [dict(row) for row in rows]

    async def list_by_task(self, task_id: str) -> list[dict]:
        """List trace summaries for a task."""
        rows = await self._db.fetch_all(
            """SELECT id, event_id, agent_role, model, prompt_tokens,
                      completion_tokens, cost_usd, duration_ms, timestamp
               FROM decision_traces WHERE task_id = ?
               ORDER BY timestamp""",
            (task_id,),
        )
        return [dict(row) for row in rows]

    def _decompress_row(self, row: dict) -> DecisionTrace:
        prompt = json.loads(zlib.decompress(row["prompt_compressed"]))
        response = zlib.decompress(row["response_compressed"]).decode()
        thinking = (
            zlib.decompress(row["thinking_compressed"]).decode()
            if row["thinking_compressed"] else None
        )
        tool_calls = [
            ToolCall(**tc)
            for tc in json.loads(row["tool_calls_json"] or "[]")
        ]
        return DecisionTrace(
            id=row["id"],
            event_id=row["event_id"],
            task_id=row["task_id"],
            sprint_id=row["sprint_id"],
            project_id=row["project_id"],
            agent_role=row["agent_role"],
            model=row["model"],
            prompt_messages=prompt,
            response_text=response,
            thinking=thinking,
            tool_calls=tool_calls,
            prompt_tokens=row["prompt_tokens"],
            completion_tokens=row["completion_tokens"],
            cost_usd=row["cost_usd"],
            duration_ms=row["duration_ms"],
            timestamp=row["timestamp"],
        )
```

### 5.4 Capturing Traces in AgentRuntime

Extend the `call_llm` method to also record decision traces:

```python
# foundrai/agents/runtime.py (modified — added to call_llm)

import time

async def call_llm(self, messages: list[dict], **kwargs) -> LLMResponse:
    # Budget check (from §3.4) ...

    start = time.monotonic()
    response = await self._llm_client.complete(messages, **kwargs)
    duration_ms = int((time.monotonic() - start) * 1000)

    # Record token usage (from §2.4) ...

    # Record decision trace
    if self._trace_store:
        trace = DecisionTrace(
            event_id=self._current_event_id,
            task_id=self._current_task_id,
            sprint_id=self._current_sprint_id,
            project_id=self._current_project_id,
            agent_role=self.role,
            model=response.model,
            prompt_messages=messages,
            response_text=response.content,
            thinking=getattr(response, "thinking", None),
            tool_calls=[
                ToolCall(tool_name=tc.name, arguments=tc.arguments)
                for tc in (response.tool_calls or [])
            ],
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            cost_usd=usage.cost_usd if usage else 0.0,
            duration_ms=duration_ms,
        )
        await self._trace_store.record(trace)

    return response
```

### 5.5 Frontend Decision Trace Viewer

```typescript
// frontend/src/components/trace/DecisionTraceViewer.tsx

interface DecisionTraceData {
  id: string;
  agentRole: string;
  model: string;
  promptMessages: Array<{ role: string; content: string }>;
  responseText: string;
  thinking: string | null;
  toolCalls: Array<{
    toolName: string;
    arguments: Record<string, unknown>;
    result: string | null;
  }>;
  promptTokens: number;
  completionTokens: number;
  costUsd: number;
  durationMs: number;
  timestamp: string;
}

const DecisionTraceViewer: React.FC<{ traceId: string }> = ({ traceId }) => {
  const [trace, setTrace] = useState<DecisionTraceData | null>(null);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  useEffect(() => {
    api.getDecisionTrace(traceId).then(setTrace);
  }, [traceId]);

  if (!trace) return <Spinner />;

  return (
    <div className="trace-viewer">
      {/* Header */}
      <div className="trace-header">
        <AgentAvatar role={trace.agentRole} size="sm" />
        <span className="trace-model">{trace.model}</span>
        <span className="trace-cost">${trace.costUsd.toFixed(4)}</span>
        <span className="trace-duration">{trace.durationMs}ms</span>
        <span className="trace-tokens">
          {trace.promptTokens}→{trace.completionTokens} tokens
        </span>
      </div>

      {/* Collapsible sections */}
      <CollapsibleSection title="💭 Thinking" defaultOpen={false}>
        <pre className="trace-thinking">{trace.thinking || "N/A"}</pre>
      </CollapsibleSection>

      <CollapsibleSection title="📨 Prompt" defaultOpen={false}>
        {trace.promptMessages.map((msg, i) => (
          <div key={i} className={`trace-message trace-${msg.role}`}>
            <strong>{msg.role}:</strong>
            <pre>{msg.content}</pre>
          </div>
        ))}
      </CollapsibleSection>

      {trace.toolCalls.length > 0 && (
        <CollapsibleSection title="🔧 Tool Calls" defaultOpen={true}>
          {trace.toolCalls.map((tc, i) => (
            <div key={i} className="trace-tool-call">
              <code>{tc.toolName}({JSON.stringify(tc.arguments)})</code>
              {tc.result && <pre className="trace-tool-result">{tc.result}</pre>}
            </div>
          ))}
        </CollapsibleSection>
      )}

      <CollapsibleSection title="📤 Response" defaultOpen={true}>
        <pre className="trace-response">{trace.responseText}</pre>
      </CollapsibleSection>
    </div>
  );
};
```

Integration with the existing feed: clicking a `FeedEntry` expands inline to show all traces associated with that event.

```typescript
// frontend/src/components/feed/FeedEntry.tsx (modified)

const FeedEntry: React.FC<{ event: Event }> = ({ event }) => {
  const [showTrace, setShowTrace] = useState(false);
  const [traceSummaries, setTraceSummaries] = useState<TraceSummary[]>([]);

  const handleExpand = async () => {
    if (!showTrace) {
      const summaries = await api.getTracesByEvent(event.id);
      setTraceSummaries(summaries);
    }
    setShowTrace(!showTrace);
  };

  return (
    <div className="feed-entry">
      {/* Existing feed entry content */}
      <div className="feed-content" onClick={handleExpand}>
        {/* ... existing ... */}
        <span className="trace-expand-icon">{showTrace ? "▼" : "▶"}</span>
      </div>

      {/* Expanded trace view */}
      {showTrace && (
        <div className="feed-traces">
          {traceSummaries.map((ts) => (
            <DecisionTraceViewer key={ts.id} traceId={ts.id} />
          ))}
        </div>
      )}
    </div>
  );
};
```

---

## 6. Communication Graph

### 6.1 Design Overview

Visualize agent-to-agent communication as an interactive graph. Nodes represent agents, edges represent message flow between them. Edge thickness/color encodes message count and types.

### 6.2 Backend: Communication Aggregation

```python
# foundrai/persistence/comm_graph.py

class CommEdge(BaseModel):
    """A directed edge in the communication graph."""
    source: str       # agent role
    target: str       # agent role
    message_count: int
    by_type: dict[str, int] = {}  # message_type -> count


class CommGraph(BaseModel):
    """Aggregated communication graph for a sprint."""
    nodes: list[str]           # agent roles
    edges: list[CommEdge]
    total_messages: int


class CommGraphBuilder:
    """Build communication graph from message bus data."""

    def __init__(self, db: Database) -> None:
        self._db = db

    async def build(self, sprint_id: str) -> CommGraph:
        """Aggregate messages into a communication graph."""
        rows = await self._db.fetch_all(
            """SELECT sender_role, recipient_role, message_type, COUNT(*) as cnt
               FROM messages
               WHERE sprint_id = ?
               GROUP BY sender_role, recipient_role, message_type""",
            (sprint_id,),
        )

        nodes: set[str] = set()
        edge_map: dict[tuple[str, str], CommEdge] = {}

        for row in rows:
            src, tgt = row["sender_role"], row["recipient_role"]
            nodes.add(src)
            nodes.add(tgt)
            key = (src, tgt)
            if key not in edge_map:
                edge_map[key] = CommEdge(source=src, target=tgt, message_count=0)
            edge = edge_map[key]
            edge.message_count += row["cnt"]
            edge.by_type[row["message_type"]] = row["cnt"]

        return CommGraph(
            nodes=sorted(nodes),
            edges=list(edge_map.values()),
            total_messages=sum(e.message_count for e in edge_map.values()),
        )
```

### 6.3 Frontend: Force-Directed Graph

Use ReactFlow (already in project) with a force-directed layout for the communication graph:

```typescript
// frontend/src/components/analytics/CommGraph.tsx

import ReactFlow, {
  Node, Edge, useNodesState, useEdgesState,
} from "reactflow";

interface CommGraphProps {
  sprintId: string;
}

const AGENT_COLORS: Record<string, string> = {
  product_manager: "#3b82f6",
  developer: "#22c55e",
  qa_engineer: "#f59e0b",
  architect: "#8b5cf6",
  designer: "#ec4899",
};

const CommGraphView: React.FC<CommGraphProps> = ({ sprintId }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    api.getCommGraph(sprintId).then((graph) => {
      // Arrange nodes in a circle
      const angleStep = (2 * Math.PI) / graph.nodes.length;
      const radius = 200;

      const rfNodes: Node[] = graph.nodes.map((role, i) => ({
        id: role,
        position: {
          x: 300 + radius * Math.cos(i * angleStep),
          y: 300 + radius * Math.sin(i * angleStep),
        },
        data: { label: formatRole(role) },
        style: {
          background: AGENT_COLORS[role] || "#6b7280",
          color: "#fff",
          borderRadius: "50%",
          width: 80,
          height: 80,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "12px",
          fontWeight: "bold",
        },
      }));

      const maxCount = Math.max(...graph.edges.map((e) => e.messageCount), 1);
      const rfEdges: Edge[] = graph.edges.map((e, i) => ({
        id: `edge-${i}`,
        source: e.source,
        target: e.target,
        label: `${e.messageCount}`,
        style: { strokeWidth: 1 + (e.messageCount / maxCount) * 5 },
        animated: true,
      }));

      setNodes(rfNodes);
      setEdges(rfEdges);
    });
  }, [sprintId]);

  return (
    <div style={{ width: "100%", height: 500 }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
      />
    </div>
  );
};
```

---

## 7. Sprint Comparison View

### 7.1 Design Overview

A table and chart view allowing users to compare metrics across multiple sprints, with trend lines showing improvement over time.

### 7.2 Backend: Sprint Comparison Data

```python
# foundrai/api/routes/analytics.py

@router.get("/projects/{project_id}/sprint-comparison")
async def get_sprint_comparison(
    project_id: str,
    db: Database = Depends(get_db),
    token_store: TokenStore = Depends(get_token_store),
) -> list[SprintComparisonRow]:
    """Get comparison data across all sprints in a project."""
    sprints = await db.fetch_all(
        """SELECT s.sprint_id, s.sprint_number, s.status, s.created_at,
                  s.completed_at, s.metrics_json
           FROM sprints s WHERE s.project_id = ?
           ORDER BY s.sprint_number""",
        (project_id,),
    )

    rows = []
    for sprint in sprints:
        metrics = json.loads(sprint["metrics_json"] or "{}")
        usage = await token_store.get_sprint_summary(sprint["sprint_id"])

        # Calculate duration
        duration_s = None
        if sprint["created_at"] and sprint["completed_at"]:
            start = datetime.fromisoformat(sprint["created_at"])
            end = datetime.fromisoformat(sprint["completed_at"])
            duration_s = (end - start).total_seconds()

        rows.append(SprintComparisonRow(
            sprint_id=sprint["sprint_id"],
            sprint_number=sprint["sprint_number"],
            task_count=metrics.get("task_count", 0),
            completed_count=metrics.get("completed_count", 0),
            failed_count=metrics.get("failed_count", 0),
            completion_rate=metrics.get("completion_rate", 0),
            quality_score=metrics.get("quality_score", 0),
            total_tokens=usage.total_tokens,
            total_cost_usd=usage.total_cost_usd,
            tokens_per_task=(
                usage.total_tokens / max(metrics.get("task_count", 1), 1)
            ),
            duration_seconds=duration_s,
        ))

    return rows
```

### 7.3 Frontend: Comparison View

```typescript
// frontend/src/components/analytics/SprintComparison.tsx

interface SprintComparisonRow {
  sprintId: string;
  sprintNumber: number;
  taskCount: number;
  completedCount: number;
  completionRate: number;
  qualityScore: number;
  totalTokens: number;
  totalCostUsd: number;
  tokensPerTask: number;
  durationSeconds: number | null;
}

const SprintComparison: React.FC<{ projectId: string }> = ({ projectId }) => {
  const [data, setData] = useState<SprintComparisonRow[]>([]);

  useEffect(() => {
    api.getSprintComparison(projectId).then(setData);
  }, [projectId]);

  return (
    <div className="sprint-comparison">
      {/* Trend charts */}
      <div className="comparison-charts">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <XAxis dataKey="sprintNumber" label={{ value: "Sprint" }} />
            <YAxis yAxisId="rate" domain={[0, 100]} />
            <YAxis yAxisId="cost" orientation="right" />
            <Line yAxisId="rate" dataKey="completionRate" stroke="#22c55e"
                  name="Completion %" />
            <Line yAxisId="rate" dataKey="qualityScore" stroke="#3b82f6"
                  name="Quality" strokeDasharray="5 5" />
            <Line yAxisId="cost" dataKey="totalCostUsd" stroke="#f59e0b"
                  name="Cost ($)" />
            <Tooltip />
            <Legend />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Comparison table */}
      <table className="comparison-table">
        <thead>
          <tr>
            <th>Sprint</th>
            <th>Tasks</th>
            <th>Completion</th>
            <th>Quality</th>
            <th>Tokens</th>
            <th>Cost</th>
            <th>Tok/Task</th>
            <th>Duration</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={row.sprintId}>
              <td>#{row.sprintNumber}</td>
              <td>{row.taskCount}</td>
              <td>{row.completionRate.toFixed(0)}%</td>
              <td>{row.qualityScore.toFixed(1)}/5</td>
              <td>{row.totalTokens.toLocaleString()}</td>
              <td>${row.totalCostUsd.toFixed(2)}</td>
              <td>{row.tokensPerTask.toFixed(0)}</td>
              <td>{formatDuration(row.durationSeconds)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

---

## 8. Error Diagnosis Tools

### 8.1 Design Overview

When an agent fails a task, capture the full error context — task state, agent state, last LLM response, error traceback — and provide a structured error panel with suggested fixes.

### 8.2 Error Log Model

```python
# foundrai/models/error_log.py

class ErrorLog(BaseModel):
    """Structured error log for agent failures."""
    id: str = Field(default_factory=generate_id)
    task_id: str
    sprint_id: str
    project_id: str
    agent_role: str

    # Error details
    error_type: str              # Exception class name
    error_message: str           # Exception message
    traceback: str               # Full traceback string

    # Context at time of failure
    task_status: str             # Task status when error occurred
    task_description: str        # Task description for context
    last_llm_response: str | None = None  # Last LLM response before failure
    agent_state: dict | None = None       # Serialized agent state

    # Diagnosis
    category: str = "unknown"    # "llm_error", "tool_error", "budget_exceeded",
                                 # "timeout", "validation_error", "dependency_failed"
    suggested_fix: str | None = None

    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
```

### 8.3 Error Capture in AgentRuntime

```python
# foundrai/agents/runtime.py (modified)

async def execute_task(self, task: Task) -> TaskResult:
    """Execute a task with full error capture on failure."""
    try:
        result = await self._do_execute(task)
        return result
    except BudgetExceededError as e:
        return await self._handle_error(task, e, category="budget_exceeded",
            suggested_fix="Increase budget or reduce task complexity")
    except TimeoutError as e:
        return await self._handle_error(task, e, category="timeout",
            suggested_fix="Increase timeout or simplify the task")
    except Exception as e:
        category = self._classify_error(e)
        suggested_fix = self._suggest_fix(e, category)
        return await self._handle_error(task, e, category=category,
            suggested_fix=suggested_fix)

async def _handle_error(
    self, task: Task, error: Exception, category: str,
    suggested_fix: str | None = None,
) -> TaskResult:
    """Capture error context and store structured error log."""
    error_log = ErrorLog(
        task_id=task.id,
        sprint_id=self._current_sprint_id,
        project_id=self._current_project_id,
        agent_role=self.role,
        error_type=type(error).__name__,
        error_message=str(error),
        traceback=traceback.format_exc(),
        task_status=task.status.value,
        task_description=task.description,
        last_llm_response=self._last_response,
        agent_state=self._serialize_state(),
        category=category,
        suggested_fix=suggested_fix,
    )
    await self._error_store.record(error_log)

    return TaskResult(status=TaskStatus.FAILED, error=str(error))

def _classify_error(self, error: Exception) -> str:
    """Classify error into a category for diagnosis."""
    error_name = type(error).__name__
    error_str = str(error).lower()

    if "rate_limit" in error_str or "429" in error_str:
        return "rate_limit"
    if "context_length" in error_str or "token" in error_str:
        return "context_overflow"
    if "timeout" in error_str:
        return "timeout"
    if "validation" in error_str or "pydantic" in error_name.lower():
        return "validation_error"
    if "tool" in error_str or "execute" in error_str:
        return "tool_error"
    return "llm_error"

SUGGESTED_FIXES: dict[str, str] = {
    "rate_limit": "Wait and retry, or switch to a different model",
    "context_overflow": "Reduce prompt size or split task into smaller subtasks",
    "timeout": "Increase timeout setting or simplify the task",
    "validation_error": "Check agent output format — may need prompt adjustment",
    "tool_error": "Check tool configuration and permissions",
    "budget_exceeded": "Increase budget allocation for this agent or sprint",
    "llm_error": "Check LLM provider status and API keys",
}

def _suggest_fix(self, error: Exception, category: str) -> str | None:
    return self.SUGGESTED_FIXES.get(category)
```

### 8.4 Error Store

```python
# foundrai/persistence/error_store.py

class ErrorStore:
    """Persistence layer for structured error logs."""

    def __init__(self, db: Database) -> None:
        self._db = db

    async def record(self, error: ErrorLog) -> None:
        await self._db.execute(
            """INSERT INTO error_logs
               (id, task_id, sprint_id, project_id, agent_role,
                error_type, error_message, traceback,
                task_status, task_description, last_llm_response,
                agent_state_json, category, suggested_fix, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (error.id, error.task_id, error.sprint_id, error.project_id,
             error.agent_role, error.error_type, error.error_message,
             error.traceback, error.task_status, error.task_description,
             error.last_llm_response,
             json.dumps(error.agent_state) if error.agent_state else None,
             error.category, error.suggested_fix, error.timestamp),
        )

    async def get_by_task(self, task_id: str) -> list[ErrorLog]:
        rows = await self._db.fetch_all(
            "SELECT * FROM error_logs WHERE task_id = ? ORDER BY timestamp",
            (task_id,),
        )
        return [self._parse_row(row) for row in rows]

    async def get_by_sprint(self, sprint_id: str) -> list[ErrorLog]:
        rows = await self._db.fetch_all(
            "SELECT * FROM error_logs WHERE sprint_id = ? ORDER BY timestamp",
            (sprint_id,),
        )
        return [self._parse_row(row) for row in rows]

    async def get_summary(self, sprint_id: str) -> dict:
        """Get error summary: count by category."""
        rows = await self._db.fetch_all(
            """SELECT category, COUNT(*) as cnt
               FROM error_logs WHERE sprint_id = ?
               GROUP BY category""",
            (sprint_id,),
        )
        return {row["category"]: row["cnt"] for row in rows}
```

### 8.5 Frontend: Error Panel

```typescript
// frontend/src/components/diagnostics/ErrorPanel.tsx

interface ErrorLogData {
  id: string;
  taskId: string;
  agentRole: string;
  errorType: string;
  errorMessage: string;
  traceback: string;
  taskDescription: string;
  lastLlmResponse: string | null;
  category: string;
  suggestedFix: string | null;
  timestamp: string;
}

const ErrorPanel: React.FC<{ taskId: string }> = ({ taskId }) => {
  const [errors, setErrors] = useState<ErrorLogData[]>([]);

  useEffect(() => {
    api.getErrorsByTask(taskId).then(setErrors);
  }, [taskId]);

  if (errors.length === 0) return null;

  return (
    <div className="error-panel">
      <h3>🔴 Errors ({errors.length})</h3>
      {errors.map((err) => (
        <div key={err.id} className={`error-entry error-${err.category}`}>
          <div className="error-header">
            <span className="error-badge">{err.category}</span>
            <AgentAvatar role={err.agentRole} size="xs" />
            <span className="error-type">{err.errorType}</span>
            <span className="error-time">
              {formatRelativeTime(err.timestamp)}
            </span>
          </div>

          <div className="error-message">{err.errorMessage}</div>

          {err.suggestedFix && (
            <div className="error-fix">
              💡 <strong>Suggested fix:</strong> {err.suggestedFix}
            </div>
          )}

          <CollapsibleSection title="Stack Trace" defaultOpen={false}>
            <pre className="error-traceback">{err.traceback}</pre>
          </CollapsibleSection>

          {err.lastLlmResponse && (
            <CollapsibleSection title="Last LLM Response" defaultOpen={false}>
              <pre className="error-llm-response">{err.lastLlmResponse}</pre>
            </CollapsibleSection>
          )}
        </div>
      ))}
    </div>
  );
};
```

---

## 9. Event Replay System

### 9.1 Design Overview

Events are already stored in an append-only log (Phase 0). The replay system adds a WebSocket-based streaming API that re-emits events at configurable speed, plus frontend playback controls.

### 9.2 Replay API (WebSocket)

```python
# foundrai/api/routes/replay.py

from fastapi import WebSocket, WebSocketDisconnect
import asyncio


class ReplayController:
    """Controls event replay for a sprint."""

    def __init__(self, events: list[dict]):
        self.events = events
        self.index = 0
        self.speed = 1.0       # 1x = real-time gaps, 10x = 10x faster
        self.playing = False
        self.min_delay = 0.05  # Minimum delay between events (50ms)

    def play(self) -> None:
        self.playing = True

    def pause(self) -> None:
        self.playing = False

    def set_speed(self, speed: float) -> None:
        self.speed = max(0.1, min(100.0, speed))

    def seek(self, index: int) -> None:
        self.index = max(0, min(len(self.events) - 1, index))

    def seek_percent(self, pct: float) -> None:
        self.index = int(len(self.events) * max(0.0, min(1.0, pct)))


@router.websocket("/ws/replay/{sprint_id}")
async def replay_sprint(websocket: WebSocket, sprint_id: str):
    await websocket.accept()

    # Load all events for the sprint
    events = await event_log.get_sprint_events(sprint_id)
    if not events:
        await websocket.send_json({"type": "error", "message": "No events found"})
        await websocket.close()
        return

    controller = ReplayController(events)

    # Send initial state
    await websocket.send_json({
        "type": "init",
        "totalEvents": len(events),
        "sprintId": sprint_id,
    })

    try:
        # Run two tasks: one for sending events, one for receiving commands
        send_task = asyncio.create_task(_send_events(websocket, controller))
        recv_task = asyncio.create_task(_recv_commands(websocket, controller))
        await asyncio.gather(send_task, recv_task)
    except WebSocketDisconnect:
        pass


async def _send_events(websocket: WebSocket, ctrl: ReplayController) -> None:
    """Stream events according to controller state."""
    while ctrl.index < len(ctrl.events):
        if not ctrl.playing:
            await asyncio.sleep(0.1)
            continue

        event = ctrl.events[ctrl.index]

        # Calculate delay based on time gap to next event
        if ctrl.index + 1 < len(ctrl.events):
            current_ts = datetime.fromisoformat(event["timestamp"])
            next_ts = datetime.fromisoformat(ctrl.events[ctrl.index + 1]["timestamp"])
            gap = (next_ts - current_ts).total_seconds()
            delay = max(ctrl.min_delay, gap / ctrl.speed)
        else:
            delay = 0

        await websocket.send_json({
            "type": "event",
            "index": ctrl.index,
            "total": len(ctrl.events),
            "event": event,
        })

        ctrl.index += 1
        if delay > 0:
            await asyncio.sleep(delay)

    # Replay complete
    await websocket.send_json({"type": "complete"})


async def _recv_commands(websocket: WebSocket, ctrl: ReplayController) -> None:
    """Receive playback commands from the client."""
    while True:
        data = await websocket.receive_json()
        cmd = data.get("command")

        if cmd == "play":
            ctrl.play()
        elif cmd == "pause":
            ctrl.pause()
        elif cmd == "speed":
            ctrl.set_speed(data.get("value", 1.0))
        elif cmd == "seek":
            ctrl.seek(data.get("index", 0))
        elif cmd == "seek_percent":
            ctrl.seek_percent(data.get("value", 0.0))
        elif cmd == "stop":
            break

        # Send state update
        await websocket.send_json({
            "type": "state",
            "index": ctrl.index,
            "total": len(ctrl.events),
            "playing": ctrl.playing,
            "speed": ctrl.speed,
        })
```

### 9.3 Frontend: Replay Controls

```typescript
// frontend/src/components/replay/ReplayControls.tsx

interface ReplayState {
  index: number;
  total: number;
  playing: boolean;
  speed: number;
}

const SPEED_OPTIONS = [0.5, 1, 2, 5, 10, 50];

const ReplayControls: React.FC<{ sprintId: string }> = ({ sprintId }) => {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [state, setState] = useState<ReplayState>({
    index: 0, total: 0, playing: false, speed: 1,
  });
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    const socket = new WebSocket(
      `${WS_BASE}/ws/replay/${sprintId}`
    );

    socket.onmessage = (msg) => {
      const data = JSON.parse(msg.data);
      switch (data.type) {
        case "init":
          setState((s) => ({ ...s, total: data.totalEvents }));
          break;
        case "event":
          setEvents((prev) => [...prev, data.event]);
          setState((s) => ({ ...s, index: data.index }));
          break;
        case "state":
          setState({
            index: data.index,
            total: data.total,
            playing: data.playing,
            speed: data.speed,
          });
          break;
        case "complete":
          setState((s) => ({ ...s, playing: false }));
          break;
      }
    };

    setWs(socket);
    return () => socket.close();
  }, [sprintId]);

  const send = (command: string, value?: number) => {
    ws?.send(JSON.stringify({ command, value }));
  };

  const progress = state.total > 0 ? state.index / state.total : 0;

  return (
    <div className="replay-controls">
      {/* Transport buttons */}
      <div className="replay-transport">
        <button onClick={() => send("seek", 0)} title="Rewind">⏮</button>
        <button
          onClick={() => send(state.playing ? "pause" : "play")}
          title={state.playing ? "Pause" : "Play"}
        >
          {state.playing ? "⏸" : "▶️"}
        </button>
        <button onClick={() => send("stop")} title="Stop">⏹</button>
      </div>

      {/* Progress bar */}
      <div className="replay-progress">
        <input
          type="range"
          min={0}
          max={100}
          value={progress * 100}
          onChange={(e) =>
            send("seek_percent", parseInt(e.target.value) / 100)
          }
        />
        <span>
          {state.index} / {state.total}
        </span>
      </div>

      {/* Speed selector */}
      <div className="replay-speed">
        {SPEED_OPTIONS.map((s) => (
          <button
            key={s}
            className={state.speed === s ? "active" : ""}
            onClick={() => send("speed", s)}
          >
            {s}x
          </button>
        ))}
      </div>

      {/* Event feed (replayed events render into existing AgentFeed) */}
      <AgentFeed events={events} isReplay />
    </div>
  );
};
```

### 9.4 REST Fallback (Non-WebSocket)

For environments where WebSocket is unavailable, provide a REST endpoint that returns paginated events:

```python
@router.get("/sprints/{sprint_id}/replay")
async def get_replay_events(
    sprint_id: str,
    offset: int = 0,
    limit: int = 50,
) -> dict:
    """Get paginated events for replay."""
    events = await event_log.get_sprint_events(sprint_id)
    return {
        "total": len(events),
        "offset": offset,
        "events": events[offset : offset + limit],
    }
```

---

## 10. Database Schema Changes

```sql
-- Token usage tracking
CREATE TABLE IF NOT EXISTS token_usage (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    sprint_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    agent_role TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd REAL NOT NULL DEFAULT 0.0,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_token_usage_sprint ON token_usage(sprint_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_project ON token_usage(project_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_agent ON token_usage(sprint_id, agent_role);
CREATE INDEX IF NOT EXISTS idx_token_usage_task ON token_usage(task_id);

-- Decision traces (compressed LLM interactions)
CREATE TABLE IF NOT EXISTS decision_traces (
    id TEXT PRIMARY KEY,
    event_id TEXT,
    task_id TEXT,
    sprint_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    agent_role TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_compressed BLOB,           -- zlib-compressed JSON
    response_compressed BLOB,         -- zlib-compressed text
    thinking_compressed BLOB,         -- zlib-compressed text (nullable)
    tool_calls_json TEXT,             -- JSON array of tool calls
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd REAL NOT NULL DEFAULT 0.0,
    duration_ms INTEGER NOT NULL DEFAULT 0,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_traces_event ON decision_traces(event_id);
CREATE INDEX IF NOT EXISTS idx_traces_task ON decision_traces(task_id);
CREATE INDEX IF NOT EXISTS idx_traces_sprint ON decision_traces(sprint_id);

-- Error logs (structured error context)
CREATE TABLE IF NOT EXISTS error_logs (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    sprint_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    agent_role TEXT NOT NULL,
    error_type TEXT NOT NULL,
    error_message TEXT NOT NULL,
    traceback TEXT,
    task_status TEXT,
    task_description TEXT,
    last_llm_response TEXT,
    agent_state_json TEXT,
    category TEXT NOT NULL DEFAULT 'unknown',
    suggested_fix TEXT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_errors_task ON error_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_errors_sprint ON error_logs(sprint_id);
CREATE INDEX IF NOT EXISTS idx_errors_category ON error_logs(sprint_id, category);

-- Budget overrides (runtime overrides of foundrai.yaml defaults)
CREATE TABLE IF NOT EXISTS budget_overrides (
    sprint_id TEXT NOT NULL,
    agent_role TEXT,              -- NULL = sprint-level budget
    budget_usd REAL NOT NULL,
    warning_threshold REAL NOT NULL DEFAULT 0.80,
    hard_limit INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (sprint_id, COALESCE(agent_role, '__sprint__'))
);

-- Messages table (if not already exists — needed for comm graph)
-- Extend existing messages table to ensure sender_role and recipient_role are indexed
CREATE INDEX IF NOT EXISTS idx_messages_sprint_roles
    ON messages(sprint_id, sender_role, recipient_role);
```

---

## 11. API Changes

### New Endpoints

| Method | Path | Description |
|---|---|---|
| **Token Usage** | | |
| `GET` | `/api/sprints/{id}/token-usage` | Token usage summary for a sprint |
| `GET` | `/api/sprints/{id}/token-usage/by-agent` | Usage breakdown by agent |
| `GET` | `/api/tasks/{id}/token-usage` | Usage for a specific task |
| `GET` | `/api/projects/{id}/token-usage` | Aggregated usage for a project |
| **Budgets** | | |
| `GET` | `/api/sprints/{id}/budget` | Get sprint budget status |
| `PUT` | `/api/sprints/{id}/budget` | Set/override sprint budget |
| `GET` | `/api/sprints/{id}/agents/{role}/budget` | Get agent budget status |
| `PUT` | `/api/sprints/{id}/agents/{role}/budget` | Set/override agent budget |
| **Analytics** | | |
| `GET` | `/api/sprints/{id}/metrics` | Sprint performance metrics |
| `GET` | `/api/sprints/{id}/agent-metrics` | Per-agent metrics for a sprint |
| `GET` | `/api/projects/{id}/sprint-comparison` | Cross-sprint comparison data |
| **Decision Traces** | | |
| `GET` | `/api/events/{id}/traces` | List trace summaries for an event |
| `GET` | `/api/tasks/{id}/traces` | List trace summaries for a task |
| `GET` | `/api/traces/{id}` | Get full decision trace (decompressed) |
| **Communication** | | |
| `GET` | `/api/sprints/{id}/comm-graph` | Communication graph for a sprint |
| **Error Diagnosis** | | |
| `GET` | `/api/tasks/{id}/errors` | Error logs for a task |
| `GET` | `/api/sprints/{id}/errors` | All errors in a sprint |
| `GET` | `/api/sprints/{id}/errors/summary` | Error count by category |
| **Replay** | | |
| `WS` | `/ws/replay/{sprint_id}` | WebSocket replay stream |
| `GET` | `/api/sprints/{id}/replay` | REST fallback (paginated events) |

### Route Registration

```python
# foundrai/api/app.py (modified)

from foundrai.api.routes import (
    analytics, token_usage, budgets, traces, comm_graph, errors, replay
)

app.include_router(analytics.router, prefix="/api", tags=["analytics"])
app.include_router(token_usage.router, prefix="/api", tags=["token-usage"])
app.include_router(budgets.router, prefix="/api", tags=["budgets"])
app.include_router(traces.router, prefix="/api", tags=["traces"])
app.include_router(comm_graph.router, prefix="/api", tags=["communication"])
app.include_router(errors.router, prefix="/api", tags=["errors"])
app.include_router(replay.router, tags=["replay"])
```

---

## 12. Frontend Changes

### New Pages

| Page | Route | Description |
|---|---|---|
| `AnalyticsPage.tsx` | `/analytics` | Main analytics dashboard |
| `ReplayPage.tsx` | `/sprints/:id/replay` | Sprint event replay |

### New Components

| Component | Directory | Description |
|---|---|---|
| `MetricCards.tsx` | `components/analytics/` | Summary metric cards (completion, quality, cost, duration) |
| `CostByAgentPie.tsx` | `components/analytics/` | Pie chart: cost by agent role |
| `CostBySprintBar.tsx` | `components/analytics/` | Bar chart: cost across sprints |
| `AgentPerformanceTable.tsx` | `components/analytics/` | Table of per-agent metrics |
| `BudgetMeter.tsx` | `components/analytics/` | Budget utilization gauge |
| `SprintComparison.tsx` | `components/analytics/` | Sprint comparison table + trends |
| `CommGraphView.tsx` | `components/analytics/` | Agent communication graph (ReactFlow) |
| `DecisionTraceViewer.tsx` | `components/trace/` | Full trace viewer (prompt → response) |
| `CollapsibleSection.tsx` | `components/shared/` | Reusable collapsible section |
| `ErrorPanel.tsx` | `components/diagnostics/` | Error details panel for failed tasks |
| `ErrorSummary.tsx` | `components/diagnostics/` | Sprint-level error summary |
| `ReplayControls.tsx` | `components/replay/` | Playback controls (play/pause/speed/seek) |
| `ReplayTimeline.tsx` | `components/replay/` | Visual timeline scrubber |

### Modified Components

| Component | Changes |
|---|---|
| `FeedEntry.tsx` | Add expandable trace viewer on click |
| `KanbanBoard.tsx` | Show error indicator on failed task cards |
| `SprintPage.tsx` | Add Analytics + Replay tabs; show budget meters |
| `DashboardPage.tsx` | Add link to Analytics; show recent cost summary |
| `App.tsx` | Add routes for `/analytics` and `/sprints/:id/replay` |
| `types/index.ts` | Add all new TypeScript interfaces |

### New API Client Methods

```typescript
// frontend/src/api/analytics.ts

export const analyticsApi = {
  getSprintMetrics: (sprintId: string) =>
    client.get<SprintMetrics>(`/sprints/${sprintId}/metrics`),

  getAgentMetrics: (sprintId: string) =>
    client.get<AgentMetrics[]>(`/sprints/${sprintId}/agent-metrics`),

  getSprintComparison: (projectId: string) =>
    client.get<SprintComparisonRow[]>(`/projects/${projectId}/sprint-comparison`),

  getTokenUsage: (sprintId: string) =>
    client.get<TokenUsageSummary>(`/sprints/${sprintId}/token-usage`),

  getBudgetStatus: (sprintId: string) =>
    client.get<BudgetStatus>(`/sprints/${sprintId}/budget`),

  getCommGraph: (sprintId: string) =>
    client.get<CommGraph>(`/sprints/${sprintId}/comm-graph`),

  getTracesByEvent: (eventId: string) =>
    client.get<TraceSummary[]>(`/events/${eventId}/traces`),

  getDecisionTrace: (traceId: string) =>
    client.get<DecisionTraceData>(`/traces/${traceId}`),

  getErrorsByTask: (taskId: string) =>
    client.get<ErrorLogData[]>(`/tasks/${taskId}/errors`),

  getErrorsSummary: (sprintId: string) =>
    client.get<Record<string, number>>(`/sprints/${sprintId}/errors/summary`),
};
```

### New Zustand Store

```typescript
// frontend/src/stores/analyticsStore.ts

interface AnalyticsState {
  sprintMetrics: SprintMetrics | null;
  agentMetrics: AgentMetrics[];
  budgetStatus: BudgetStatus | null;
  comparison: SprintComparisonRow[];
  loading: boolean;

  fetchSprintAnalytics: (sprintId: string) => Promise<void>;
  fetchComparison: (projectId: string) => Promise<void>;
}

export const useAnalyticsStore = create<AnalyticsState>((set) => ({
  sprintMetrics: null,
  agentMetrics: [],
  budgetStatus: null,
  comparison: [],
  loading: false,

  fetchSprintAnalytics: async (sprintId) => {
    set({ loading: true });
    const [metrics, agents, budget] = await Promise.all([
      analyticsApi.getSprintMetrics(sprintId),
      analyticsApi.getAgentMetrics(sprintId),
      analyticsApi.getBudgetStatus(sprintId),
    ]);
    set({
      sprintMetrics: metrics,
      agentMetrics: agents,
      budgetStatus: budget,
      loading: false,
    });
  },

  fetchComparison: async (projectId) => {
    set({ loading: true });
    const comparison = await analyticsApi.getSprintComparison(projectId);
    set({ comparison, loading: false });
  },
}));
```

---

## 13. Testing Strategy

### Unit Tests

| Test File | What It Tests |
|---|---|
| `test_cost_tracker.py` | Cost calculation for various models, fallback pricing |
| `test_token_store.py` | Token usage recording, aggregation queries |
| `test_budget.py` | Budget status calculation, threshold detection |
| `test_budget_enforcement.py` | AgentRuntime budget checks, BudgetExceededError |
| `test_trace_store.py` | Trace recording, compression/decompression roundtrip |
| `test_comm_graph.py` | Communication graph aggregation from message data |
| `test_error_store.py` | Error log recording, classification, suggested fixes |
| `test_error_classification.py` | Error classifier for all known categories |
| `test_replay_controller.py` | ReplayController play/pause/speed/seek logic |

### Integration Tests

| Test File | What It Tests |
|---|---|
| `test_integration_observability.py` | Full sprint run → verify token usage, traces, and errors all recorded |
| `test_integration_budget.py` | Sprint with tight budget → verify enforcement and task skipping |
| `test_integration_replay.py` | Run sprint → replay via WebSocket → verify event order and timing |
| `test_api_analytics.py` | All analytics API endpoints with test data |
| `test_api_traces.py` | Trace API endpoints, including decompression |

### Frontend Tests

| Test File | What It Tests |
|---|---|
| `AnalyticsPage.test.tsx` | Page renders with mock data, charts display |
| `BudgetMeter.test.tsx` | Correct colors/status for ok/warning/exceeded |
| `DecisionTraceViewer.test.tsx` | Trace expansion, collapsible sections |
| `ErrorPanel.test.tsx` | Error display, suggested fixes shown |
| `ReplayControls.test.tsx` | Transport controls, speed selection |
| `CommGraphView.test.tsx` | Graph renders with nodes and edges |
| `SprintComparison.test.tsx` | Table and chart render with comparison data |

### E2E Tests

| Test | What It Tests |
|---|---|
| `e2e_analytics_flow.py` | Navigate to analytics → verify charts and data → drill into agent |
| `e2e_trace_expansion.py` | Click feed entry → expand trace → verify prompt/response visible |
| `e2e_replay.py` | Open replay → play → pause → seek → verify events render correctly |
| `e2e_error_diagnosis.py` | View failed task → open error panel → verify traceback and fix shown |

---

## Implementation Order

Recommended build sequence (4 weeks):

| Week | Deliverables |
|---|---|
| **Week 12** | Token cost tracking + Token budget system + DB migrations |
| **Week 13** | Decision trace viewer + Error diagnosis tools |
| **Week 14** | Analytics dashboard + Sprint comparison + Communication graph |
| **Week 15** | Event replay system + Integration testing + Polish |

Each feature is independently deployable — cost tracking provides value immediately, even before the dashboard exists.

---

## Migration Notes

- All new tables use `CREATE TABLE IF NOT EXISTS` — safe to run on existing databases
- No changes to existing tables — fully additive schema
- Compressed trace storage keeps DB size manageable (~70-80% compression on typical LLM prompts/responses)
- Budget system is opt-in: without `budgets` config, no enforcement occurs
- Replay system reads from existing event log — no additional write-time cost
