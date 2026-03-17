import { useEffect, useState } from 'react';
import type { RetroResponse } from '../../types';

interface RetrospectiveViewProps {
  sprintId: string;
}

export function RetrospectiveView({ sprintId }: RetrospectiveViewProps) {
  const [retro, setRetro] = useState<RetroResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch(`/api/sprints/${sprintId}/retrospective`)
      .then((r) => {
        if (!r.ok) throw new Error('No retrospective data');
        return r.json();
      })
      .then(setRetro)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [sprintId]);

  if (loading) return <div className="p-4 text-gray-500">Loading retrospective...</div>;
  if (error) return <div className="p-4 text-gray-500">No retrospective data available yet.</div>;
  if (!retro) return null;

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-semibold">Sprint Retrospective</h2>

      {retro.went_well.length > 0 && (
        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
          <h3 className="font-medium text-green-800 dark:text-green-300 mb-2">
            ✅ What Went Well
          </h3>
          <ul className="list-disc list-inside space-y-1 text-sm text-green-700 dark:text-green-400">
            {retro.went_well.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {retro.went_wrong.length > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
          <h3 className="font-medium text-red-800 dark:text-red-300 mb-2">
            ❌ What Went Wrong
          </h3>
          <ul className="list-disc list-inside space-y-1 text-sm text-red-700 dark:text-red-400">
            {retro.went_wrong.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {retro.action_items.length > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
          <h3 className="font-medium text-blue-800 dark:text-blue-300 mb-2">
            🎯 Action Items
          </h3>
          <ul className="list-disc list-inside space-y-1 text-sm text-blue-700 dark:text-blue-400">
            {retro.action_items.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="text-sm text-gray-500">
        {retro.learnings_count} learnings stored for future sprints
      </div>
    </div>
  );
}
