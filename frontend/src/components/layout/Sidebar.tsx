import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { listProjects } from '../../api/projects';
import { listSprints } from '../../api/sprints';
import type { ProjectResponse, SprintResponse } from '../../types';
import { StatusBadge } from '../shared/StatusBadge';
import { cn } from '../../utils/cn';

export function Sidebar() {
  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [sprints, setSprints] = useState<SprintResponse[]>([]);
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const { sprintId } = useParams();

  useEffect(() => {
    listProjects().then((data) => {
      setProjects(data.projects);
      if (data.projects.length > 0 && !selectedProject) {
        setSelectedProject(data.projects[0].project_id);
      }
    }).catch(() => {});
  }, [selectedProject]);

  useEffect(() => {
    if (selectedProject) {
      listSprints(selectedProject).then((data) => {
        setSprints(data.sprints);
      }).catch(() => {});
    }
  }, [selectedProject]);

  return (
    <aside className="w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col">
      <div className="p-4 border-b border-gray-200 dark:border-gray-800">
        <Link to="/" className="flex items-center gap-2">
          <span className="text-xl">🚀</span>
          <span className="font-bold text-lg">FoundrAI</span>
        </Link>
      </div>

      <div className="p-3">
        <h3 className="text-xs font-semibold uppercase text-gray-400 mb-2">Projects</h3>
        {projects.map((p) => (
          <button
            key={p.project_id}
            onClick={() => setSelectedProject(p.project_id)}
            className={cn(
              'w-full text-left px-3 py-2 rounded text-sm',
              selectedProject === p.project_id
                ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
                : 'hover:bg-gray-100 dark:hover:bg-gray-800'
            )}
          >
            {p.name}
          </button>
        ))}
        {projects.length === 0 && (
          <p className="text-xs text-gray-400 px-3">No projects yet</p>
        )}
      </div>

      <div className="p-3 space-y-1">
        <Link
          to="/analytics"
          className="flex items-center gap-2 px-3 py-2 rounded text-sm hover:bg-gray-100 dark:hover:bg-gray-800"
        >
          <span>📊</span>
          <span>Analytics</span>
        </Link>
        <Link
          to="/settings"
          className="flex items-center gap-2 px-3 py-2 rounded text-sm hover:bg-gray-100 dark:hover:bg-gray-800"
        >
          <span>⚙️</span>
          <span>Settings</span>
        </Link>
      </div>

      <div className="p-3 flex-1 overflow-y-auto">
        <h3 className="text-xs font-semibold uppercase text-gray-400 mb-2">Sprints</h3>
        {sprints.map((s) => (
          <Link
            key={s.sprint_id}
            to={`/sprints/${s.sprint_id}`}
            className={cn(
              'block px-3 py-2 rounded text-sm mb-1',
              sprintId === s.sprint_id
                ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
                : 'hover:bg-gray-100 dark:hover:bg-gray-800'
            )}
          >
            <div className="flex items-center justify-between">
              <span>Sprint #{s.sprint_number}</span>
              <StatusBadge status={s.status} />
            </div>
            <p className="text-xs text-gray-500 mt-0.5 truncate">{s.goal}</p>
          </Link>
        ))}
        {sprints.length === 0 && (
          <p className="text-xs text-gray-400 px-3">No sprints</p>
        )}
      </div>
    </aside>
  );
}
