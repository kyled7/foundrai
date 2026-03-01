import { useSprintStore } from '../../stores/sprintStore';
import { KanbanColumn } from './KanbanColumn';
import type { TaskStatus } from '../../types';

const COLUMNS: { key: string; title: string; statuses: TaskStatus[]; color: string }[] = [
  { key: 'backlog',     title: 'Backlog',     statuses: ['backlog', 'blocked'], color: 'gray' },
  { key: 'in_progress', title: 'In Progress', statuses: ['in_progress'],        color: 'blue' },
  { key: 'in_review',   title: 'In Review',   statuses: ['in_review'],          color: 'yellow' },
  { key: 'done',        title: 'Done',        statuses: ['done'],               color: 'green' },
  { key: 'failed',      title: 'Failed',      statuses: ['failed'],             color: 'red' },
];

export function SprintBoard() {
  const tasks = useSprintStore((s) => s.tasks);

  return (
    <div className="flex gap-4 overflow-x-auto p-4 h-full">
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
  );
}
