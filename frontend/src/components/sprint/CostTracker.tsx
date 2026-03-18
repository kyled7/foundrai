import { formatCost } from '@/lib/utils';

interface CostTrackerProps {
  totalCost: number;
  byAgent?: Record<string, { cost_usd: number }>;
}

export function CostTracker({ totalCost, byAgent = {} }: CostTrackerProps) {
  const agents = Object.entries(byAgent);
  const maxCost = Math.max(...agents.map(([, v]) => v.cost_usd), 0.01);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold text-muted uppercase tracking-wider">Cost</h3>
        <span className="text-foreground text-sm font-medium">{formatCost(totalCost)}</span>
      </div>
      {agents.length > 0 && (
        <div className="space-y-1">
          {agents.map(([role, data]) => (
            <div key={role} className="flex items-center gap-2 text-xs">
              <span className="text-muted w-12 truncate capitalize">{role.split('_')[0]}</span>
              <div className="flex-1 h-1.5 bg-border rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary/60 rounded-full"
                  style={{ width: `${(data.cost_usd / maxCost) * 100}%` }}
                />
              </div>
              <span className="text-muted w-10 text-right">{formatCost(data.cost_usd)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
