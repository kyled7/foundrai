import { useApprovalStore } from '../../stores/approvalStore';

interface Props {
  onReview?: () => void;
}

export function ApprovalBanner({ onReview }: Props) {
  const pendingCount = useApprovalStore((s) => s.pendingCount);

  if (pendingCount === 0) return null;

  return (
    <div role="alert" aria-live="polite" className="bg-amber-50 dark:bg-amber-900/20 border-b border-amber-200 dark:border-amber-800 px-4 py-2 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className="text-amber-600 text-lg">⚠️</span>
        <span className="text-sm font-medium text-amber-800 dark:text-amber-200">
          {pendingCount} approval{pendingCount > 1 ? 's' : ''} waiting for your decision
        </span>
      </div>
      {onReview && (
        <button
          onClick={onReview}
          className="text-sm text-amber-700 dark:text-amber-300 hover:underline font-medium"
        >
          Review →
        </button>
      )}
    </div>
  );
}
