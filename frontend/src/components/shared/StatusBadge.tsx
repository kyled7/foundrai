import { cn } from '@/lib/utils';

const STATUS_STYLES: Record<string, string> = {
  backlog: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
  in_progress: 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300',
  in_review: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-300',
  done: 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300',
  failed: 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300',
  blocked: 'bg-gray-200 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  created: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
  planning: 'bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300',
  executing: 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300',
  reviewing: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-300',
  completed: 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300',
  cancelled: 'bg-gray-200 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  pending: 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300',
  approved: 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300',
  rejected: 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300',
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
        STATUS_STYLES[status] ?? 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
        className
      )}
    >
      {status.replace('_', ' ')}
    </span>
  );
}
