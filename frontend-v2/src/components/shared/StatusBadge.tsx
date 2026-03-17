import { cn } from '@/lib/utils';

const STATUS_STYLES: Record<string, string> = {
  backlog: 'bg-gray-100 text-gray-700',
  in_progress: 'bg-blue-100 text-blue-700',
  in_review: 'bg-yellow-100 text-yellow-700',
  done: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
  blocked: 'bg-gray-200 text-gray-600',
  created: 'bg-gray-100 text-gray-700',
  planning: 'bg-purple-100 text-purple-700',
  executing: 'bg-blue-100 text-blue-700',
  reviewing: 'bg-yellow-100 text-yellow-700',
  completed: 'bg-green-100 text-green-700',
  cancelled: 'bg-gray-200 text-gray-600',
  pending: 'bg-amber-100 text-amber-700',
  approved: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
};

interface Props {
  status: string;
  size?: 'sm' | 'md';
  className?: string;
}

export function StatusBadge({ status, size = 'sm', className }: Props) {
  return (
    <span
      role="status"
      className={cn(
        'inline-flex items-center rounded-full font-medium capitalize',
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm',
        STATUS_STYLES[status] ?? 'bg-gray-100 text-gray-700',
        className
      )}
    >
      {status.replace('_', ' ')}
    </span>
  );
}
