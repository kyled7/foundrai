import { cn, formatCost } from '@/lib/utils';
import type { CostSavingsEstimate as CostSavingsEstimateType, RecommendationConfidence } from '@/lib/types';
import { TrendingDown, TrendingUp, Sparkles, AlertCircle, CheckCircle } from 'lucide-react';

interface CostSavingsEstimateProps {
  estimate: CostSavingsEstimateType;
  loading?: boolean;
  className?: string;
}

function getConfidenceColor(confidence: RecommendationConfidence): string {
  switch (confidence) {
    case 'high':
      return 'text-green-600 dark:text-green-400';
    case 'medium':
      return 'text-yellow-600 dark:text-yellow-400';
    case 'low':
      return 'text-orange-600 dark:text-orange-400';
    case 'insufficient_data':
      return 'text-gray-400 dark:text-gray-500';
    default:
      return 'text-gray-400 dark:text-gray-500';
  }
}

function getQualityImpactIcon(impact: string) {
  switch (impact) {
    case 'improved':
      return <CheckCircle size={16} className="text-green-500" />;
    case 'degraded':
      return <AlertCircle size={16} className="text-red-500" />;
    default:
      return null;
  }
}

function getQualityImpactColor(impact: string): string {
  switch (impact) {
    case 'improved':
      return 'text-green-600 dark:text-green-400';
    case 'degraded':
      return 'text-red-600 dark:text-red-400';
    default:
      return 'text-gray-600 dark:text-gray-400';
  }
}

export function CostSavingsEstimate({ estimate, loading, className }: CostSavingsEstimateProps) {
  if (loading) {
    return (
      <div className={cn('bg-card border border-border rounded-lg p-4', className)}>
        <div className="flex items-center gap-2 mb-3">
          <div className="w-5 h-5 animate-pulse bg-border rounded" />
          <div className="h-6 w-48 animate-pulse bg-border rounded" />
        </div>
        <div className="space-y-2">
          <div className="h-4 w-full animate-pulse bg-border rounded" />
          <div className="h-4 w-3/4 animate-pulse bg-border rounded" />
        </div>
      </div>
    );
  }

  const {
    current_total_cost,
    recommended_total_cost,
    total_savings_usd,
    savings_percentage,
    role_breakdown,
    quality_impact,
    quality_score_change,
    based_on_tasks,
    confidence
  } = estimate;

  const hasSavings = total_savings_usd > 0;

  return (
    <div
      className={cn(
        'rounded-lg p-4 border transition-colors',
        hasSavings
          ? 'bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800'
          : 'bg-card border-border',
        className
      )}
    >
      <div className="flex items-center gap-2 mb-3">
        <Sparkles size={18} className="text-yellow-500" />
        <h3 className="text-lg font-semibold text-foreground">Cost Savings Estimate</h3>
      </div>

      {hasSavings ? (
        <div className="mb-4 p-3 bg-background/50 rounded border border-border/50">
          <p className="text-sm text-muted mb-1">Potential Savings</p>
          <div className="flex items-baseline gap-2">
            <p className="text-3xl font-bold text-green-600 dark:text-green-400">
              {savings_percentage.toFixed(0)}%
            </p>
            <TrendingDown size={24} className="text-green-600 dark:text-green-400" />
          </div>
          <p className="text-sm text-foreground mt-1">
            Save <span className="font-semibold">{formatCost(total_savings_usd)}</span> per sprint
          </p>
        </div>
      ) : (
        <div className="mb-4 p-3 bg-background/50 rounded border border-border/50">
          <p className="text-sm text-muted">
            Current configuration is already cost-optimized.
          </p>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="p-2 bg-background/50 rounded border border-border/50">
          <p className="text-xs text-muted mb-1">Current Cost</p>
          <p className="font-semibold text-foreground">{formatCost(current_total_cost)}</p>
        </div>
        <div className="p-2 bg-background/50 rounded border border-border/50">
          <p className="text-xs text-muted mb-1">Recommended Cost</p>
          <p className="font-semibold text-foreground">{formatCost(recommended_total_cost)}</p>
        </div>
      </div>

      {Object.keys(role_breakdown).length > 0 && (
        <div className="mb-4">
          <p className="text-xs font-medium text-muted mb-2">Per-Role Breakdown:</p>
          <div className="space-y-2">
            {Object.entries(role_breakdown).map(([role, breakdown]) => {
              const roleSavings = breakdown.savings;
              return (
                <div key={role} className="flex items-center justify-between text-sm">
                  <span className="text-foreground capitalize">{role.replace('_', ' ')}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-muted text-xs">
                      {formatCost(breakdown.current_cost)} → {formatCost(breakdown.recommended_cost)}
                    </span>
                    {roleSavings > 0 && (
                      <span className="text-green-600 dark:text-green-400 font-semibold text-xs">
                        -{formatCost(roleSavings)}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="mb-3 p-2 bg-background/50 rounded border border-border/50">
        <div className="flex items-center justify-between mb-1">
          <p className="text-xs text-muted">Quality Impact</p>
          <div className="flex items-center gap-1">
            {getQualityImpactIcon(quality_impact)}
            <span className={cn('text-xs font-semibold capitalize', getQualityImpactColor(quality_impact))}>
              {quality_impact}
            </span>
          </div>
        </div>
        {quality_score_change !== 0 && (
          <div className="flex items-center gap-1 text-xs">
            {quality_score_change > 0 ? (
              <TrendingUp size={12} className="text-green-500" />
            ) : (
              <TrendingDown size={12} className="text-red-500" />
            )}
            <span className="text-foreground">
              {quality_score_change > 0 ? '+' : ''}{quality_score_change.toFixed(1)}% quality score
            </span>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between text-xs">
        <span className="text-muted">
          Based on {based_on_tasks} task{based_on_tasks !== 1 ? 's' : ''}
        </span>
        <span className={cn('font-semibold', getConfidenceColor(confidence))}>
          {confidence.replace('_', ' ').toUpperCase()} CONFIDENCE
        </span>
      </div>
    </div>
  );
}
