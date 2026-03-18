import { useDroppable } from '@dnd-kit/core';
import type { Task } from '@/lib/types';
import { TaskCard } from './TaskCard';
import { cn } from '@/lib/utils';

const COLOR_MAP: Record<string, string> = {
  gray: 'border-t-gray-400',
  blue: 'border-t-blue-400',
  yellow: 'border-t-yellow-400',
  green: 'border-t-green-400',
  red: 'border-t-red-400',
};

interface Props {
  columnId: string;
  title: string;
  color: string;
  tasks: Task[];
  count: number;
}

export function KanbanColumn({ columnId, title, color, tasks, count }: Props) {
  const { setNodeRef, isOver } = useDroppable({
    id: columnId,
  });

  return (
    <div className={cn(
      'flex-shrink-0 w-[240px] md:w-[280px] xl:flex-1 xl:min-w-[220px] xl:max-w-[320px] bg-gray-100 dark:bg-gray-900 rounded-lg border-t-2 flex flex-col',
      COLOR_MAP[color] ?? 'border-t-gray-400'
    )}>
      <div className="p-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold">{title}</h3>
        <span className="text-xs bg-gray-200 dark:bg-gray-700 rounded-full px-2 py-0.5">
          {count}
        </span>
      </div>
      <div
        ref={setNodeRef}
        className={cn(
          'flex-1 overflow-y-auto p-2 space-y-2 transition-colors',
          isOver && 'bg-blue-50 dark:bg-blue-900/20'
        )}
      >
        {tasks.map((task) => (
          <TaskCard key={task.task_id} task={task} />
        ))}
      </div>
    </div>
  );
}
