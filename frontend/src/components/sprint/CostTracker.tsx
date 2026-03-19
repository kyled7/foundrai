import { useEffect, useState } from 'react';
import { useSprintCost } from '@/hooks/use-sprint-cost';
import { formatCost } from '@/lib/utils';

interface CostTrackerProps {
  sprintId: string;
}

export function CostTracker({ sprintId }: CostTrackerProps) {
  const { data: costData, isLoading } = useSprintCost({ sprintId });
  const [isUpdating, setIsUpdating] = useState(false);

  const totalCost = costData?.total_cost_usd ?? 0;
  const byAgent = costData?.by_agent ?? {};
  const agents = Object.entries(byAgent);
  const maxCost = Math.max(...agents.map(([, v]) => v.cost_usd), 0.01);

  // Trigger animation pulse when cost data changes
  useEffect(() => {
    if (costData && totalCost > 0) {
      setIsUpdating(true);
      const timer = setTimeout(() => setIsUpdating(false), 600);
      return () => clearTimeout(timer);
    }
  }, [costData?.total_cost_usd]);

  if (isLoading && !costData) {
    return (
      <div className="space-y-2 animate-pulse">
        <div className="flex items-center justify-between">
          <div className="h-4 w-12 bg-muted/20 rounded" />
          <div className="h-4 w-16 bg-muted/20 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold text-muted uppercase tracking-wider">Cost</h3>
        <span
          className={`text-foreground text-sm font-medium transition-all duration-300 ${
            isUpdating ? 'scale-110 text-primary' : 'scale-100'
          }`}
        >
          {formatCost(totalCost)}
        </span>
      </div>
      {agents.length > 0 && (
        <div className="space-y-1">
          {agents.map(([role, data]) => (
            <div key={role} className="flex items-center gap-2 text-xs">
              <span className="text-muted w-12 truncate capitalize">{role.split('_')[0]}</span>
              <div className="flex-1 h-1.5 bg-border rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary/60 rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${(data.cost_usd / maxCost) * 100}%` }}
                />
              </div>
              <span className="text-muted w-10 text-right transition-colors duration-300">
                {formatCost(data.cost_usd)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
