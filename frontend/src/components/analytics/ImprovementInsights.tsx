import { StatCard } from './StatCard';
import { TrendingUp, Target, DollarSign, Zap } from 'lucide-react';
import type { SprintComparison } from '@/lib/types';

interface ImprovementInsightsProps {
  data: SprintComparison[];
}

interface ImprovementMetric {
  label: string;
  currentValue: number;
  previousValue: number;
  format: 'currency' | 'percent' | 'number' | 'duration';
  icon: React.ReactNode;
  higherIsBetter: boolean;
}

function calculateImprovement(current: number, previous: number, higherIsBetter: boolean): { value: number; direction: 'up' | 'down' } | undefined {
  if (previous === 0) return undefined;
  const percentChange = ((current - previous) / previous) * 100;
  const isPositive = higherIsBetter ? percentChange > 0 : percentChange < 0;
  return {
    value: Math.abs(percentChange),
    direction: isPositive ? 'up' : 'down'
  };
}

export function ImprovementInsights({ data }: ImprovementInsightsProps) {
  if (data.length < 2) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 flex items-center justify-center h-48 text-muted text-sm">
        Need at least 2 sprints to show improvement metrics
      </div>
    );
  }

  const firstSprint = data[0];
  const latestSprint = data[data.length - 1];

  const costPerTask = (sprint: SprintComparison) =>
    sprint.completed_count > 0 ? sprint.total_cost / sprint.completed_count : 0;

  const metrics: ImprovementMetric[] = [
    {
      label: 'Velocity (Tasks/Sprint)',
      currentValue: latestSprint.completed_count,
      previousValue: firstSprint.completed_count,
      format: 'number',
      icon: <Zap size={18} />,
      higherIsBetter: true
    },
    {
      label: 'Quality (Pass Rate)',
      currentValue: latestSprint.pass_rate / 100,
      previousValue: firstSprint.pass_rate / 100,
      format: 'percent',
      icon: <Target size={18} />,
      higherIsBetter: true
    },
    {
      label: 'Cost Efficiency ($/Task)',
      currentValue: costPerTask(latestSprint),
      previousValue: costPerTask(firstSprint),
      format: 'currency',
      icon: <DollarSign size={18} />,
      higherIsBetter: false
    }
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <TrendingUp size={20} className="text-green-400" />
        <h3 className="text-sm font-medium text-foreground">
          Improvement: Sprint {firstSprint.sprint_number} → Sprint {latestSprint.sprint_number}
        </h3>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {metrics.map((metric, idx) => {
          const trend = calculateImprovement(
            metric.currentValue,
            metric.previousValue,
            metric.higherIsBetter
          );
          return (
            <StatCard
              key={idx}
              label={metric.label}
              value={metric.currentValue}
              icon={metric.icon}
              format={metric.format}
              trend={trend}
            />
          );
        })}
      </div>
    </div>
  );
}
