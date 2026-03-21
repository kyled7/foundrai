import { useState } from 'react';
import { useSprintComparison } from '@/hooks/use-analytics';
import { StatCard } from './StatCard';
import { MetricFilters, type MetricType } from './MetricFilters';
import { ImprovementInsights } from './ImprovementInsights';
import { CostTrendChart } from './CostTrendChart';
import { QualityTrendChart } from './QualityTrendChart';
import { CostEfficiencyChart } from './CostEfficiencyChart';
import { ExportMenu } from './ExportMenu';
import { PageSkeleton } from '@/components/shared/LoadingSkeleton';
import { TrendingUp, Target, DollarSign, Zap } from 'lucide-react';

interface SprintComparisonDashboardProps {
  projectId: string;
}

export function SprintComparisonDashboard({ projectId }: SprintComparisonDashboardProps) {
  const [dateRange, setDateRange] = useState<{ from: string; to: string } | null>(null);
  const [metricType, setMetricType] = useState<MetricType>('all');

  const sprintComparisonQuery = useSprintComparison(projectId);

  if (sprintComparisonQuery.isLoading) return <PageSkeleton />;

  const sprints = sprintComparisonQuery.data?.sprints ?? [];

  // Filter by date range (if date is available in sprint data)
  const filteredSprints = dateRange
    ? sprints.filter(s => {
        // TODO: Add date filtering when sprint comparison data includes dates
        return true;
      })
    : sprints;

  // Calculate summary statistics
  const totalSprints = filteredSprints.length;
  const avgCompletion = totalSprints > 0
    ? filteredSprints.reduce((a, s) => a + s.pass_rate / 100, 0) / totalSprints
    : 0;
  const avgCost = totalSprints > 0
    ? filteredSprints.reduce((a, s) => a + s.total_cost, 0) / totalSprints
    : 0;
  const totalTasksCompleted = filteredSprints.reduce((a, s) => a + s.completed_count, 0);

  // Prepare chart data
  const velocityData = filteredSprints.map(s => ({
    sprint_id: s.sprint_id,
    sprint_number: s.sprint_number,
    completed: s.completed_count,
    failed: s.failed_count,
  }));

  const costData = filteredSprints.map(s => ({
    sprint_id: s.sprint_id,
    sprint_number: s.sprint_number,
    total_cost: s.total_cost,
  }));

  const qualityData = filteredSprints.map(s => ({
    sprint_id: s.sprint_id,
    sprint_number: s.sprint_number,
    pass_rate: s.pass_rate,
  }));

  const efficiencyData = filteredSprints.map(s => ({
    sprint_id: s.sprint_id,
    sprint_number: s.sprint_number,
    cost_per_task: s.completed_count > 0 ? s.total_cost / s.completed_count : 0,
  }));

  // Determine which charts to show based on metric type
  const showVelocity = metricType === 'all' || metricType === 'velocity';
  const showQuality = metricType === 'all' || metricType === 'quality';
  const showCost = metricType === 'all' || metricType === 'cost';

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <h1 className="text-2xl font-bold text-foreground">Sprint Comparison</h1>
        <ExportMenu projectId={projectId} />
      </div>

      {/* Filters */}
      <MetricFilters
        dateRange={dateRange}
        onDateRangeChange={setDateRange}
        metricType={metricType}
        onMetricTypeChange={setMetricType}
      />

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Sprints"
          value={totalSprints}
          icon={<TrendingUp size={18} />}
        />
        <StatCard
          label="Avg Completion Rate"
          value={avgCompletion}
          icon={<Target size={18} />}
          format="percent"
        />
        <StatCard
          label="Avg Sprint Cost"
          value={avgCost}
          icon={<DollarSign size={18} />}
          format="currency"
        />
        <StatCard
          label="Total Tasks Done"
          value={totalTasksCompleted}
          icon={<Zap size={18} />}
        />
      </div>

      {/* Improvement Insights */}
      <ImprovementInsights data={filteredSprints} />

      {/* Velocity Charts */}
      {showVelocity && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="text-sm font-medium text-foreground mb-4">Velocity Trend</h3>
            <div className="h-64 flex items-center justify-center text-muted text-sm">
              {velocityData.length > 0 ? (
                <div className="w-full">
                  <div className="text-xs text-muted-foreground mb-2">
                    Tasks completed per sprint over time
                  </div>
                  {/* TODO: Create dedicated VelocityTrendChart component */}
                  <div className="grid grid-cols-2 gap-2">
                    {velocityData.slice(-4).map(d => (
                      <div key={d.sprint_id} className="bg-background rounded p-3">
                        <div className="text-xs text-muted-foreground">Sprint {d.sprint_number}</div>
                        <div className="text-lg font-semibold text-green-400">{d.completed}</div>
                        <div className="text-xs text-red-400">{d.failed} failed</div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                'No velocity data yet'
              )}
            </div>
          </div>
          <QualityTrendChart data={qualityData} />
        </div>
      )}

      {/* Quality Charts */}
      {showQuality && !showVelocity && (
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1">
            <QualityTrendChart data={qualityData} />
          </div>
        </div>
      )}

      {/* Cost Charts */}
      {showCost && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <CostTrendChart data={costData} />
          <CostEfficiencyChart data={efficiencyData} />
        </div>
      )}
    </div>
  );
}
