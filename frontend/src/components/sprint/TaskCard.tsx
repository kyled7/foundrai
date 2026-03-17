import { useDraggable } from '@dnd-kit/core';
import { useState } from 'react';
import type { TaskResponse } from '../../types';
import { AgentAvatar } from '../shared/AgentAvatar';
import { StatusBadge } from '../shared/StatusBadge';
import { cn } from '../../utils/cn';

interface Props {
  task: TaskResponse;
  isDragging?: boolean;
}

export function TaskCard({ task, isDragging = false }: Props) {
  const [expanded, setExpanded] = useState(false);

  const { attributes, listeners, setNodeRef, transform, isDragging: isBeingDragged } = useDraggable({
    id: task.task_id,
    disabled: isDragging,
  });

  const style = transform
    ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
      }
    : undefined;

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
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-sm font-medium leading-tight">{task.title}</h4>
        <StatusBadge status={task.status} />
      </div>

      <div className="flex items-center gap-1.5 mt-2">
        <AgentAvatar role={task.assigned_to} size="sm" />
        <span className="text-xs text-gray-500 capitalize">
          {task.assigned_to.replace('_', ' ')}
        </span>
      </div>

      <div className="flex items-center gap-1 mt-2">
        {Array.from({ length: Math.max(1, 6 - task.priority) }, (_, i) => (
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
              <pre className="whitespace-pre-wrap mt-1">{task.result.output}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
