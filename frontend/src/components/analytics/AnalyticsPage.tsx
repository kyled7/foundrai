import { useState } from 'react';
import { useProjectCost, useCostOverTime, useSprintHistory, useSprintComparison, useAgentPerformance, useLearnings } from '@/hooks/use-analytics';
import { StatCard } from './StatCard';
import { DateRangePicker } from './DateRangePicker';
import { CostOverTimeChart } from './CostOverTimeChart';
import { CostTrendChart } from './CostTrendChart';
import { AgentCostPieChart } from './AgentCostPieChart';
import { SprintVelocityChart } from './SprintVelocityChart';
import { AgentPerformanceTable } from './AgentPerformanceTable';
import { LearningsTimeline } from './LearningsTimeline';
import { DollarSign, Zap, Target, Clock } from 'lucide-react';
import { PageSkeleton } from '@/components/shared/LoadingSkeleton';

interface ProjectAnalyticsPageProps {
  projectId: string;
}

export function ProjectAnalyticsPage({ projectId }: ProjectAnalyticsPageProps) {
  const [dateRange, setDateRange] = useState<{ from: string; to: string } | null>(null);

  const costQuery = useProjectCost(projectId);
  const costOverTimeQuery = useCostOverTime(projectId);
  const sprintHistoryQuery = useSprintHistory(projectId);
  const sprintComparisonQuery = useSprintComparison(projectId);
  const agentPerfQuery = useAgentPerformance(projectId);
  const learningsQuery = useLearnings(projectId);

  const isLoading = costQuery.isLoading || costOverTimeQuery.isLoading || sprintHistoryQuery.isLoading;

  if (isLoading) return <PageSkeleton />;

  const cost = costQuery.data;
  const costData = costOverTimeQuery.data ?? [];
  const sprints = sprintHistoryQuery.data ?? [];
  const sprintComparisons = sprintComparisonQuery.data?.sprints ?? [];
  const agents = agentPerfQuery.data ?? [];
  const learnings = learningsQuery.data?.learnings ?? [];

  // Filter by date range
  const filteredCost = dateRange
    ? costData.filter(p => p.date >= dateRange.from && p.date <= dateRange.to)
    : costData;
  const filteredSprints = dateRange
    ? sprints.filter(s => s.created_at.slice(0, 10) >= dateRange.from && s.created_at.slice(0, 10) <= dateRange.to)
    : sprints;
  const filteredComparisons = dateRange
    ? sprintComparisons.filter(s => s.sprint_number >= 0) // TODO: Add date filtering when available
    : sprintComparisons;

  const totalSprints = filteredSprints.length;
  const avgCompletion = totalSprints > 0 ? filteredSprints.reduce((a, s) => a + s.completion_rate, 0) / totalSprints : 0;
  const avgDuration = totalSprints > 0
    ? filteredSprints.reduce((a, s) => a + (s.duration_seconds ?? 0), 0) / totalSprints
    : 0;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <h1 className="text-2xl font-bold text-foreground">Analytics</h1>
        <DateRangePicker value={dateRange} onChange={setDateRange} />
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Spend" value={cost?.total_cost_usd ?? 0} icon={<DollarSign size={18} />} format="currency" />
        <StatCard label="Sprints Run" value={totalSprints} icon={<Zap size={18} />} />
        <StatCard label="Completion Rate" value={avgCompletion} icon={<Target size={18} />} format="percent" />
        <StatCard label="Avg Duration" value={avgDuration} icon={<Clock size={18} />} format="duration" />
      </div>

      {/* Charts row */}
      <div className="flex flex-col lg:flex-row gap-4">
        <div className="flex-1">
          <CostOverTimeChart data={filteredCost} />
        </div>
        <div className="w-full lg:w-96">
          <AgentCostPieChart data={cost?.by_agent ?? {}} />
        </div>
      </div>

      {/* Cost Trend */}
      <div className="flex flex-col lg:flex-row gap-4">
        <div className="flex-1">
          <CostTrendChart data={filteredComparisons} />
        </div>
      </div>

      {/* Velocity + Performance */}
      <div className="flex flex-col lg:flex-row gap-4">
        <div className="flex-1">
          <SprintVelocityChart data={filteredSprints} />
        </div>
        <div className="w-full lg:w-96">
          <AgentPerformanceTable data={agents} />
        </div>
      </div>

      {/* Learnings */}
      <LearningsTimeline learnings={learnings} />
    </div>
  );
}
