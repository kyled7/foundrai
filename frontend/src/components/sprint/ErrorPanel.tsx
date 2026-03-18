import { useEffect, useState } from 'react';

interface ErrorEntry {
  error_id: number;
  task_id: string | null;
  sprint_id: string | null;
  agent_role: string;
  error_type: string;
  error_message: string;
  traceback: string;
  context_json: string;
  suggested_fix: string;
  timestamp: string;
}

const TYPE_COLORS: Record<string, string> = {
  rate_limit: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  context_overflow: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  timeout: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  tool_error: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  parse_error: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  unknown: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
};

interface Props {
  taskId?: string;
  sprintId?: string;
}

export function ErrorPanel({ taskId, sprintId }: Props) {
  const [errors, setErrors] = useState<ErrorEntry[]>([]);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    const url = taskId ? `/tasks/${taskId}/errors` : sprintId ? `/sprints/${sprintId}/errors` : null;
    if (!url) return;

    // Use the api client's request method directly
    fetch(`/api${url}`)
      .then((res) => res.json())
      .then((d: { errors: ErrorEntry[] }) => setErrors(d.errors))
      .catch(() => {});
  }, [taskId, sprintId]);

  if (errors.length === 0) return null;

  return (
    <div className="space-y-2">
      {errors.map(err => (
        <div key={err.error_id} className="border border-red-200 dark:border-red-800 rounded p-3 text-sm">
          <div className="flex items-center gap-2">
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${TYPE_COLORS[err.error_type] || TYPE_COLORS.unknown}`}>
              {err.error_type}
            </span>
            <span className="text-gray-500 text-xs">{err.agent_role}</span>
          </div>
          <p className="mt-1 text-red-700 dark:text-red-300">{err.error_message}</p>
          {err.suggested_fix && (
            <p className="mt-1 text-green-700 dark:text-green-300 text-xs">💡 {err.suggested_fix}</p>
          )}
          <button
            onClick={() => setExpandedId(expandedId === err.error_id ? null : err.error_id)}
            className="text-xs text-gray-500 mt-1 hover:underline"
          >
            {expandedId === err.error_id ? 'Hide traceback' : 'Show traceback'}
          </button>
          {expandedId === err.error_id && err.traceback && (
            <pre className="mt-2 bg-gray-50 dark:bg-gray-900 rounded p-2 text-xs overflow-x-auto whitespace-pre-wrap">
              {err.traceback}
            </pre>
          )}
        </div>
      ))}
    </div>
  );
}
