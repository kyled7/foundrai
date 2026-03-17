import { cn } from '../../utils/cn';

interface Props {
  budgetUsd: number;
  spentUsd: number;
  percentageUsed: number;
  isWarning: boolean;
  isExceeded: boolean;
}

export function BudgetMeter({ budgetUsd, spentUsd, percentageUsed, isWarning, isExceeded }: Props) {
  const barWidth = Math.min(percentageUsed, 100);

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-5">
      <h3 className="text-sm font-semibold mb-2">Sprint Budget</h3>
      {budgetUsd <= 0 ? (
        <p className="text-gray-400 text-sm">No budget set (unlimited)</p>
      ) : (
        <>
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>${spentUsd.toFixed(4)} spent</span>
            <span>${budgetUsd.toFixed(2)} budget</span>
          </div>
          <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className={cn(
                'h-full rounded-full transition-all',
                isExceeded
                  ? 'bg-red-500'
                  : isWarning
                    ? 'bg-yellow-500'
                    : 'bg-green-500',
              )}
              style={{ width: `${barWidth}%` }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-1">{percentageUsed.toFixed(1)}% used</p>
        </>
      )}
    </div>
  );
}
