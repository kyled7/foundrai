import { useSprintStore } from '../../stores/sprintStore';
import { useApprovalStore } from '../../stores/approvalStore';
import { StatusBadge } from '../shared/StatusBadge';

export function Header() {
  const sprint = useSprintStore((s) => s.sprint);
  const pendingCount = useApprovalStore((s) => s.pendingCount);

  return (
    <header className="h-14 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 flex items-center px-4 justify-between">
      <div className="flex items-center gap-3">
        {sprint ? (
          <>
            <h1 className="font-semibold">Sprint #{sprint.sprint_number}</h1>
            <StatusBadge status={sprint.status} size="md" />
            <span className="text-sm text-gray-500 truncate max-w-md">{sprint.goal}</span>
          </>
        ) : (
          <h1 className="font-semibold">FoundrAI Dashboard</h1>
        )}
      </div>

      <div className="flex items-center gap-3">
        {pendingCount > 0 && (
          <span className="bg-amber-100 text-amber-800 text-xs font-medium px-2.5 py-1 rounded-full">
            ⚠️ {pendingCount} pending
          </span>
        )}
      </div>
    </header>
  );
}
