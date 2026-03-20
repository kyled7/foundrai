import { cn, formatCost } from '@/lib/utils';
import type { ModelRecommendation, RecommendationConfidence } from '@/lib/types';
import { AgentAvatar } from '../shared/AgentAvatar';
import { Sparkles, TrendingUp, TrendingDown, CheckCircle, XCircle } from 'lucide-react';

interface ModelRecommendationCardProps {
  recommendation: ModelRecommendation;
  loading?: boolean;
  onAccept?: (recommendation: ModelRecommendation) => void;
  onDismiss?: (recommendation: ModelRecommendation) => void;
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

function getConfidenceBg(confidence: RecommendationConfidence): string {
  switch (confidence) {
    case 'high':
      return 'bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800';
    case 'medium':
      return 'bg-yellow-50 dark:bg-yellow-950 border-yellow-200 dark:border-yellow-800';
    case 'low':
      return 'bg-orange-50 dark:bg-orange-950 border-orange-200 dark:border-orange-800';
    case 'insufficient_data':
      return 'bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700';
    default:
      return 'bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700';
  }
}

export function ModelRecommendationCard({
  recommendation,
  loading,
  onAccept,
  onDismiss,
  className
}: ModelRecommendationCardProps) {
  if (loading) {
    return (
      <div className={cn('bg-card border border-border rounded-lg p-4', className)}>
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 animate-pulse bg-border rounded-full" />
          <div className="flex-1">
            <div className="h-5 w-24 animate-pulse bg-border rounded mb-1" />
            <div className="h-4 w-16 animate-pulse bg-border rounded" />
          </div>
        </div>
        <div className="space-y-2">
          <div className="h-4 w-full animate-pulse bg-border rounded" />
          <div className="h-4 w-3/4 animate-pulse bg-border rounded" />
        </div>
      </div>
    );
  }

  const {
    agent_role,
    recommended_model,
    current_model,
    confidence,
    reasoning,
    expected_quality_score,
    expected_cost_per_task,
    expected_success_rate,
    alternative_models
  } = recommendation;

  const costChange = current_model && recommendation.performance_metrics
    ? expected_cost_per_task - recommendation.performance_metrics.avg_cost_per_task
    : 0;

  const qualityChange = current_model && recommendation.performance_metrics
    ? expected_quality_score - recommendation.performance_metrics.quality_score
    : 0;

  return (
    <div
      className={cn(
        'rounded-lg p-4 border transition-colors',
        getConfidenceBg(confidence),
        className
      )}
    >
      <div className="flex items-center gap-3 mb-3">
        <AgentAvatar role={agent_role} size="md" />
        <div className="flex-1">
          <h3 className="font-medium capitalize text-foreground flex items-center gap-2">
            {agent_role.replace('_', ' ')}
            <Sparkles size={14} className="text-yellow-500" />
          </h3>
          <p className={cn('text-sm font-semibold', getConfidenceColor(confidence))}>
            {confidence.replace('_', ' ').toUpperCase()} CONFIDENCE
          </p>
        </div>
      </div>

      <div className="mb-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-muted">Current Model</span>
          <span className="text-sm font-medium text-foreground">
            {current_model || 'Not set'}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted">Recommended</span>
          <span className="text-sm font-bold text-foreground">{recommended_model}</span>
        </div>
      </div>

      <div className="mb-3 p-2 bg-background/50 rounded border border-border/50">
        <p className="text-xs text-muted mb-1">Reasoning:</p>
        <p className="text-xs text-foreground">{reasoning}</p>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-3 text-sm">
        <div>
          <p className="text-muted text-xs">Quality</p>
          <p className="font-semibold text-foreground flex items-center gap-1">
            {expected_quality_score.toFixed(1)}%
            {qualityChange !== 0 && (
              qualityChange > 0 ? (
                <TrendingUp size={12} className="text-green-500" />
              ) : (
                <TrendingDown size={12} className="text-red-500" />
              )
            )}
          </p>
        </div>
        <div>
          <p className="text-muted text-xs">Cost/Task</p>
          <p className="font-semibold text-foreground flex items-center gap-1">
            {formatCost(expected_cost_per_task)}
            {costChange !== 0 && (
              costChange < 0 ? (
                <TrendingDown size={12} className="text-green-500" />
              ) : (
                <TrendingUp size={12} className="text-red-500" />
              )
            )}
          </p>
        </div>
        <div>
          <p className="text-muted text-xs">Success</p>
          <p className="font-semibold text-foreground">
            {expected_success_rate.toFixed(1)}%
          </p>
        </div>
      </div>

      {alternative_models.length > 0 && (
        <div className="mb-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs font-medium text-muted mb-1">Alternatives:</p>
          <div className="flex flex-wrap gap-1">
            {alternative_models.map((model) => (
              <span
                key={model}
                className="text-xs px-2 py-1 bg-background/50 border border-border/50 rounded text-foreground"
              >
                {model}
              </span>
            ))}
          </div>
        </div>
      )}

      {(onAccept || onDismiss) && (
        <div className="flex gap-2 mt-3">
          {onAccept && (
            <button
              onClick={() => onAccept(recommendation)}
              className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded transition-colors"
            >
              <CheckCircle size={14} />
              Accept
            </button>
          )}
          {onDismiss && (
            <button
              onClick={() => onDismiss(recommendation)}
              className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-gray-600 hover:bg-gray-700 text-white text-sm font-medium rounded transition-colors"
            >
              <XCircle size={14} />
              Dismiss
            </button>
          )}
        </div>
      )}
    </div>
  );
}
