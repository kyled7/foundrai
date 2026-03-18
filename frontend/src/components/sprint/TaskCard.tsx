import { useDraggable } from '@dnd-kit/core';
import { useState, useMemo, useCallback, memo } from 'react';
import type { Task } from '@/lib/types';
import { AgentAvatar } from '@/components/shared/AgentAvatar';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { cn } from '@/lib/utils';

interface Props {
  task: Task;
  isDragging?: boolean;
}

export const TaskCard = memo(function TaskCard({ task, isDragging = false }: Props) {
  const [expanded, setExpanded] = useState(false);

  const { attributes, listeners, setNodeRef, transform, isDragging: isBeingDragged } = useDraggable({
    id: task.task_id,
    disabled: isDragging,
  });

  const style = useMemo(
    () =>
      transform
        ? {
            transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
          }
        : undefined,
    [transform]
  );

  const priorityDots = useMemo(
    () => Array.from({ length: Math.max(1, 6 - task.priority) }, (_, i) => i),
    [task.priority]
  );

  const assignedToLabel = useMemo(
    () => task.assigned_to.replace('_', ' '),
    [task.assigned_to]
  );

  const toggleExpanded = useCallback(() => {
    setExpanded((prev) => !prev);
  }, []);

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={cn(
        'bg-white dark:bg-gray-800 rounded-lg border p-3 shadow-sm',
        'hover:shadow-md transition-shadow cursor-pointer',
        task.status === 'failed' && 'border-red-300',
        isBeingDragged && 'opacity-30'
      )}
      onClick={toggleExpanded}
    >
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-sm font-medium leading-tight">{task.title}</h4>
        <StatusBadge status={task.status} />
      </div>

      <div className="flex items-center gap-1.5 mt-2">
        <AgentAvatar role={task.assigned_to} size="sm" />
        <span className="text-xs text-gray-500 capitalize">
          {assignedToLabel}
        </span>
      </div>

      <div className="flex items-center gap-1 mt-2">
        {priorityDots.map((i) => (
          <div key={i} className="w-1.5 h-1.5 rounded-full bg-orange-400" />
        ))}
      </div>

      {expanded && (
        <div className="mt-3 pt-3 border-t text-xs text-gray-600 dark:text-gray-400 space-y-2">
          <p>{task.description}</p>
          {task.acceptance_criteria.length > 0 && (
            <ul className="list-disc list-inside space-y-0.5">
              {task.acceptance_criteria.map((ac, i) => (
                <li key={i}>{ac}</li>
              ))}
            </ul>
          )}
          {task.result && (
            <div className="bg-gray-50 dark:bg-gray-900 rounded p-2 mt-2">
              <span className="font-medium">Result:</span>
              <pre className="whitespace-pre-wrap mt-1">{JSON.stringify(task.result, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
});
