import { useQuery } from '@tanstack/react-query';
import { useSprintStore } from '@/stores/sprintStore';
import { KanbanColumn } from './KanbanColumn';
import { BudgetWarning } from './BudgetWarning';
import { api } from '@/lib/api';
import type { TaskStatus } from '@/lib/types';

const COLUMNS: { key: string; title: string; statuses: TaskStatus[]; color: string }[] = [
  { key: 'backlog',     title: 'Backlog',     statuses: ['pending', 'blocked'], color: 'gray' },
  { key: 'in_progress', title: 'In Progress', statuses: ['in_progress'],        color: 'blue' },
  { key: 'completed',   title: 'Completed',   statuses: ['completed'],          color: 'green' },
  { key: 'failed',      title: 'Failed',      statuses: ['failed'],             color: 'red' },
];

interface SprintBoardProps {
  sprintId?: string;
}

export function SprintBoard({ sprintId }: SprintBoardProps = {}) {
  const tasks = useSprintStore((s) => s.tasks);

  // Fetch budget status for warning banner
  const { data: budgetStatus } = useQuery({
    queryKey: ['sprint', sprintId, 'budget'],
    queryFn: () => api.analytics.budget(sprintId!),
    enabled: !!sprintId,
    refetchInterval: 10000, // Refetch every 10 seconds
  });

  return (
    <div className="flex flex-col h-full" role="region" aria-label="Sprint task board">
      {/* Budget warning banner */}
      {sprintId && budgetStatus && (budgetStatus.is_warning || budgetStatus.is_exceeded) && (
        <div className="px-4 pt-4">
          <BudgetWarning budgetStatus={budgetStatus} sprintId={sprintId} />
        </div>
      )}

      {/* Kanban columns */}
      <div className="flex gap-4 overflow-x-auto p-4 flex-1">
        {COLUMNS.map((col) => {
          const filtered = tasks.filter((t) => col.statuses.includes(t.status));
          return (
            <KanbanColumn
              key={col.key}
              title={col.title}
              color={col.color}
              tasks={filtered}
              count={filtered.length}
            />
          );
        })}
      </div>
    </div>
  );
}
