import { useEffect, useState } from 'react';
import { MetricCard } from '../components/analytics/MetricCard';
import { CostByAgentChart } from '../components/analytics/CostByAgentChart';
import { CostBySprintChart } from '../components/analytics/CostBySprintChart';
import { AgentPerformanceTable } from '../components/analytics/AgentPerformanceTable';
import { BudgetMeter } from '../components/analytics/BudgetMeter';
import { CommGraph } from '../components/analytics/CommGraph';
import { SprintComparison } from '../components/analytics/SprintComparison';
import { listProjects } from '../api/projects';
import { listSprints } from '../api/sprints';
import { getProjectCost, getSprintBudget } from '../api/analytics';
import type { CostBreakdown, BudgetStatus } from '../api/analytics';

export function AnalyticsPage() {
  const [projectId, setProjectId] = useState<string | null>(null);
  const [latestSprintId, setLatestSprintId] = useState<string | null>(null);
  const [projectCost, setProjectCost] = useState<CostBreakdown | null>(null);
  const [budget, setBudget] = useState<BudgetStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load first project + its sprints automatically
  useEffect(() => {
    listProjects()
      .then((data) => {
        if (data.projects.length > 0) {
          const pid = data.projects[0].project_id;
          setProjectId(pid);
        }
      })
      .catch((e) => setError(e.message));
  }, []);

  // Load project cost and latest sprint when project changes
  useEffect(() => {
    if (!projectId) return;

    getProjectCost(projectId)
      .then(setProjectCost)
      .catch(() => setProjectCost(null));

    listSprints(projectId)
      .then((data) => {
        if (data.sprints.length > 0) {
          const sid = data.sprints[0].sprint_id;
          setLatestSprintId(sid);
          getSprintBudget(sid)
            .then(setBudget)
            .catch(() => setBudget(null));
        }
      })
      .catch(() => {});
  }, [projectId]);

  const agentRows = projectCost
    ? Object.entries(projectCost.by_agent).map(([agent, v]) => ({
        agent,
        tasks: v.call_count,
        passRate: '—',
        tokens: v.total_tokens,
        cost: v.total_cost,
      }))
    : [];

  const sprintCount = projectCost?.by_sprint ? Object.keys(projectCost.by_sprint).length : 0;
  const avgCostPerSprint =
    sprintCount > 0 ? (projectCost?.total_cost ?? 0) / sprintCount : 0;

  return (
    <div className="p-6 overflow-y-auto h-full space-y-6">
      <h1 className="text-xl font-bold">Analytics</h1>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 p-3 rounded text-sm">
          {error}
        </div>
      )}

      {/* Metric cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Cost"
          value={`$${(projectCost?.total_cost ?? 0).toFixed(4)}`}
          icon="💰"
        />
        <MetricCard
          title="Total Tokens"
          value={(projectCost?.total_tokens ?? 0).toLocaleString()}
          icon="🔤"
        />
        <MetricCard
          title="Avg Cost/Sprint"
          value={`$${avgCostPerSprint.toFixed(4)}`}
          icon="📊"
        />
        <MetricCard
          title="API Calls"
          value={(projectCost?.call_count ?? 0).toLocaleString()}
          icon="📞"
        />
      </div>

      {/* Budget meter */}
      {budget && (
        <BudgetMeter
          budgetUsd={budget.budget_usd}
          spentUsd={budget.spent_usd}
          percentageUsed={budget.percentage_used}
          isWarning={budget.is_warning}
          isExceeded={budget.is_exceeded}
        />
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <CostByAgentChart data={projectCost?.by_agent ?? {}} />
        <CostBySprintChart data={projectCost?.by_sprint ?? {}} />
      </div>

      {/* Agent performance table */}
      <AgentPerformanceTable agents={agentRows} />

      {/* Communication Graph */}
      <CommGraph sprintId={latestSprintId} />

      {/* Sprint Comparison */}
      <SprintComparison projectId={projectId} />

      {!projectCost && !error && (
        <p className="text-gray-400 text-sm text-center py-8">
          No analytics data yet. Cost data will appear as agents run sprints.
        </p>
      )}
    </div>
  );
}
