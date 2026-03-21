import { useDroppable } from '@dnd-kit/core';
import type { Task } from '@/lib/types';
import { TaskCard } from './TaskCard';
import { cn } from '../../utils/cn';

const COLOR_MAP: Record<string, string> = {
  gray: 'border-t-gray-400',
  blue: 'border-t-blue-400',
  yellow: 'border-t-yellow-400',
  green: 'border-t-green-400',
  red: 'border-t-red-400',
};

interface Props {
  id: string;
  title: string;
  color: string;
  tasks: Task[];
  count: number;
}

export function DroppableColumn({ id, title, color, tasks, count }: Props) {
  const { setNodeRef, isOver } = useDroppable({
    id,
  });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'flex-1 min-w-[220px] max-w-[300px] bg-gray-100 dark:bg-gray-900 rounded-lg border-t-2 flex flex-col transition-colors',
        COLOR_MAP[color] ?? 'border-t-gray-400',
        isOver && 'ring-2 ring-blue-500 ring-opacity-50 bg-blue-50 dark:bg-blue-900/20'
      )}
    >
      <div className="p-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold">{title}</h3>
        <span className="text-xs bg-gray-200 dark:bg-gray-700 rounded-full px-2 py-0.5">
          {count}
        </span>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {tasks.map((task) => (
          <TaskCard key={task.task_id} task={task} />
        ))}
      </div>
    </div>
  );
}
