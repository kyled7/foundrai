import { useState } from 'react';
import type { Task } from '@/lib/types';
import { AgentAvatar } from '@/components/shared/AgentAvatar';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { CostDisplay } from '@/components/shared/CostDisplay';
import { cn } from '@/lib/utils';

interface Props {
  task: Task;
}

export function TaskCard({ task }: Props) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={cn(
        'bg-white dark:bg-gray-800 rounded-lg border p-3 shadow-sm',
        'hover:shadow-md transition-shadow cursor-pointer',
        task.status === 'failed' && 'border-red-300'
      )}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-sm font-medium leading-tight">{task.title}</h4>
        <StatusBadge status={task.status} />
      </div>

      <div className="flex items-center justify-between mt-2">
        <div className="flex items-center gap-1.5">
          <AgentAvatar role={task.assigned_to} size="sm" />
          <span className="text-xs text-gray-500 capitalize">
            {task.assigned_to.replace('_', ' ')}
          </span>
        </div>
        {task.cost_usd !== undefined && task.cost_usd > 0 && (
          <CostDisplay costUsd={task.cost_usd} className="text-xs" />
        )}
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
          {task.cost_usd !== undefined && task.cost_usd > 0 && (
            <div className="flex items-center gap-2 pt-2">
              <span className="font-medium">Cost:</span>
              <CostDisplay
                costUsd={task.cost_usd}
                tokens={task.tokens_used}
                className="text-xs"
              />
            </div>
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
}
