import { AlertTriangle, AlertCircle, X, ArrowRightLeft } from 'lucide-react';
import { useState } from 'react';
import { formatCost } from '@/lib/utils';

interface ModelSwitchInfo {
  from_model: string;
  to_model: string;
  agent_role?: string;
  reason?: string;
}

interface BudgetWarningProps {
  budgetStatus: {
    budget_usd: number;
    spent_usd: number;
    remaining_usd: number;
    percentage_used: number;
    is_warning: boolean;
    is_exceeded: boolean;
  };
  sprintId: string;
  dismissible?: boolean;
  modelSwitch?: ModelSwitchInfo;
}

/**
 * BudgetWarning banner component that appears when budget thresholds are exceeded.
 * - Warning banner (yellow) when configurable threshold is reached (default 80%)
 * - Error banner (red) at 100% usage (exceeded)
 * - Info banner (blue) when automatic model tier-down occurs
 */
export function BudgetWarning({ budgetStatus, sprintId, dismissible = true, modelSwitch }: BudgetWarningProps) {
  const [isBudgetDismissed, setIsBudgetDismissed] = useState(false);
  const [isModelSwitchDismissed, setIsModelSwitchDismissed] = useState(false);

  const isExceeded = budgetStatus.is_exceeded;
  const percentage = Math.round(budgetStatus.percentage_used);
  const showBudgetWarning = (budgetStatus.is_warning || budgetStatus.is_exceeded) && !isBudgetDismissed;
  const showModelSwitch = modelSwitch && !isModelSwitchDismissed;

  // Don't show anything if both are dismissed or not applicable
  if (!showBudgetWarning && !showModelSwitch) {
    return null;
  }

  return (
    <div className="space-y-2">
      {/* Model Switch Banner */}
      {showModelSwitch && (
        <div
          role="alert"
          className="
            relative rounded-lg p-3 border
            bg-blue-500/10 border-blue-500/30 text-blue-400
            animate-in fade-in slide-in-from-top-2 duration-300
          "
        >
          <div className="flex items-start gap-3">
            {/* Icon */}
            <div className="flex-shrink-0 mt-0.5">
              <ArrowRightLeft className="h-5 w-5" />
            </div>

            {/* Content */}
            <div className="flex-1 space-y-1">
              <div className="flex items-center justify-between gap-2">
                <h4 className="text-sm font-semibold">
                  Model Switched
                </h4>
                {dismissible && (
                  <button
                    onClick={() => setIsModelSwitchDismissed(true)}
                    className="text-current hover:opacity-70 transition-opacity"
                    aria-label="Dismiss model switch notification"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>

              <p className="text-xs opacity-90">
                {modelSwitch.agent_role && (
                  <>
                    <span className="font-semibold capitalize">{modelSwitch.agent_role}</span> agent
                    {' '}
                  </>
                )}
                automatically switched to a more cost-effective model:{' '}
                <span className="font-semibold">{modelSwitch.from_model}</span>
                {' '}&rarr;{' '}
                <span className="font-semibold">{modelSwitch.to_model}</span>
                {modelSwitch.reason && ` (${modelSwitch.reason})`}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Budget Warning Banner */}
      {showBudgetWarning && (
        <div
          role="alert"
          className={`
            relative rounded-lg p-3 border
            ${
              isExceeded
                ? 'bg-red-500/10 border-red-500/30 text-red-400'
                : 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
            }
            animate-in fade-in slide-in-from-top-2 duration-300
          `}
        >
          <div className="flex items-start gap-3">
            {/* Icon */}
            <div className="flex-shrink-0 mt-0.5">
              {isExceeded ? (
                <AlertCircle className="h-5 w-5" />
              ) : (
                <AlertTriangle className="h-5 w-5" />
              )}
            </div>

            {/* Content */}
            <div className="flex-1 space-y-1">
              <div className="flex items-center justify-between gap-2">
                <h4 className="text-sm font-semibold">
                  {isExceeded ? 'Budget Exceeded' : 'Budget Warning'}
                </h4>
                {dismissible && (
                  <button
                    onClick={() => setIsBudgetDismissed(true)}
                    className="text-current hover:opacity-70 transition-opacity"
                    aria-label="Dismiss budget warning"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>

              <p className="text-xs opacity-90">
                {isExceeded ? (
                  <>
                    Sprint budget has been exceeded. You've spent{' '}
                    <span className="font-semibold">{formatCost(budgetStatus.spent_usd)}</span> of{' '}
                    <span className="font-semibold">{formatCost(budgetStatus.budget_usd)}</span>{' '}
                    ({percentage}% used).
                  </>
                ) : (
                  <>
                    Sprint is approaching budget limit ({percentage}% used).{' '}
                    <span className="font-semibold">{formatCost(budgetStatus.remaining_usd)}</span>{' '}
                    remaining of <span className="font-semibold">{formatCost(budgetStatus.budget_usd)}</span>.
                  </>
                )}
              </p>

              {/* Progress bar */}
              <div className="mt-2 h-1.5 bg-black/20 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ease-out ${
                    isExceeded ? 'bg-red-500' : 'bg-yellow-500'
                  }`}
                  style={{ width: `${Math.min(percentage, 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
