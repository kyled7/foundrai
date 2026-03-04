import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listProjects } from '../api/projects';
import { listSprints } from '../api/sprints';
import type { ProjectResponse, SprintResponse } from '../types';
import { StatusBadge } from '../components/shared/StatusBadge';

export function DashboardPage() {
  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [recentSprints, setRecentSprints] = useState<SprintResponse[]>([]);

  useEffect(() => {
    listProjects().then((data) => {
      setProjects(data.projects);
      // Load sprints from first project
      if (data.projects.length > 0) {
        listSprints(data.projects[0].project_id).then((s) => {
          setRecentSprints(s.sprints);
        }).catch(() => {});
      }
    }).catch(() => {});
  }, []);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      {projects.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-5xl mb-4">🚀</p>
          <h2 className="text-xl font-semibold mb-2">Welcome to FoundrAI</h2>
          <p className="text-gray-500 mb-4">
            Get started by running <code className="bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded">foundrai init my-project</code> in your terminal.
          </p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            {projects.map((p) => (
              <div key={p.project_id} className="bg-white dark:bg-gray-800 rounded-lg border p-4 shadow-sm">
                <h3 className="font-semibold">{p.name}</h3>
                <p className="text-sm text-gray-500 mt-1">{p.description || 'No description'}</p>
                <p className="text-xs text-gray-400 mt-2">{p.sprint_count} sprint{p.sprint_count !== 1 ? 's' : ''}</p>
              </div>
            ))}
          </div>

          {recentSprints.length > 0 && (
            <>
              <h2 className="text-lg font-semibold mb-3">Recent Sprints</h2>
              <div className="space-y-2">
                {recentSprints.map((s) => (
                  <Link
                    key={s.sprint_id}
                    to={`/sprints/${s.sprint_id}`}
                    className="block bg-white dark:bg-gray-800 rounded-lg border p-4 shadow-sm hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Sprint #{s.sprint_number}</span>
                      <StatusBadge status={s.status} />
                    </div>
                    <p className="text-sm text-gray-500 mt-1">{s.goal}</p>
                    <div className="flex gap-4 mt-2 text-xs text-gray-400">
                      <span>{s.metrics?.total_tasks || 0} tasks</span>
                      <span>{s.metrics?.completed_tasks || 0} completed</span>
                    </div>
                  </Link>
                ))}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
