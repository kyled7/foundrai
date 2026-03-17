import { useState } from 'react';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { ChevronDown, ChevronUp } from 'lucide-react';
import type { Task } from '@/lib/types';

interface TaskListProps {
  tasks: Task[];
}

export function TaskList({ tasks }: TaskListProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <div className="space-y-1">
      <h3 className="text-xs font-semibold text-muted uppercase tracking-wider mb-2">Tasks ({tasks.length})</h3>
      {tasks.map((task) => {
        const isExpanded = expandedId === task.task_id;
        return (
          <div key={task.task_id} className="bg-background rounded-md overflow-hidden">
            <button
              onClick={() => setExpandedId(isExpanded ? null : task.task_id)}
              className="flex items-center gap-2 w-full px-2 py-1.5 text-left hover:bg-border/30"
            >
              <StatusBadge status={task.status} className="text-[10px]" />
              <span className="text-foreground text-xs flex-1 truncate">{task.title}</span>
              {isExpanded ? <ChevronUp size={12} className="text-muted" /> : <ChevronDown size={12} className="text-muted" />}
            </button>
            {isExpanded && (
              <div className="px-2 pb-2 space-y-1">
                <p className="text-muted text-xs">{task.description}</p>
                {task.assigned_to && (
                  <p className="text-xs text-muted">Assigned to: <span className="text-foreground">{task.assigned_to}</span></p>
                )}
                {task.acceptance_criteria.length > 0 && (
                  <div>
                    <p className="text-xs text-muted mb-0.5">Acceptance criteria:</p>
                    <ul className="text-xs text-muted list-disc list-inside">
                      {task.acceptance_criteria.map((c, i) => <li key={i}>{c}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
