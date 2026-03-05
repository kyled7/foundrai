import { cn } from '@/lib/utils';

const statusConfig: Record<string, { color: string; label: string }> = {
  created: { color: 'bg-gray-500/20 text-gray-400', label: 'Created' },
  planning: { color: 'bg-blue-500/20 text-blue-400', label: 'Planning' },
  in_progress: { color: 'bg-yellow-500/20 text-yellow-400', label: 'In Progress' },
  review: { color: 'bg-purple-500/20 text-purple-400', label: 'Review' },
  completed: { color: 'bg-green-500/20 text-green-400', label: 'Completed' },
  failed: { color: 'bg-red-500/20 text-red-400', label: 'Failed' },
  cancelled: { color: 'bg-gray-500/20 text-gray-500', label: 'Cancelled' },
  pending: { color: 'bg-gray-500/20 text-gray-400', label: 'Pending' },
  blocked: { color: 'bg-orange-500/20 text-orange-400', label: 'Blocked' },
};

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status] ?? { color: 'bg-gray-500/20 text-gray-400', label: status };
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium', config.color, className)}>
      {config.label}
    </span>
  );
}
