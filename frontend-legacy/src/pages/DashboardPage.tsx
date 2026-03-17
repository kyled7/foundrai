import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { listProjects, createProject } from '../api/projects';
import { listSprints, createSprint } from '../api/sprints';
import { executeSprint } from '../api/execution';
import type { ProjectResponse, SprintResponse } from '../types';
import { StatusBadge } from '../components/shared/StatusBadge';

export function DashboardPage() {
  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [recentSprints, setRecentSprints] = useState<SprintResponse[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [showNewSprint, setShowNewSprint] = useState(false);
  const [showNewProject, setShowNewProject] = useState(false);
  const [sprintGoal, setSprintGoal] = useState('');
  const [projectName, setProjectName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  const loadData = () => {
    listProjects().then((data) => {
      setProjects(data.projects);
      if (data.projects.length > 0) {
        const pid = selectedProjectId ?? data.projects[0].project_id;
        setSelectedProjectId(pid);
        listSprints(pid).then((s) => {
          setRecentSprints(s.sprints);
        }).catch(() => {});
      }
    }).catch(() => {});
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      listSprints(selectedProjectId).then((s) => {
        setRecentSprints(s.sprints);
      }).catch(() => {});
    }
  }, [selectedProjectId]);

  const handleCreateProject = async () => {
    if (!projectName.trim()) return;
    setSubmitting(true);
    try {
      const p = await createProject(projectName.trim());
      setProjectName('');
      setShowNewProject(false);
      setSelectedProjectId(p.project_id);
      loadData();
    } catch {
      // Could show error toast
    } finally {
      setSubmitting(false);
    }
  };

  const handleStartSprint = async () => {
    if (!sprintGoal.trim() || !selectedProjectId) return;
    setSubmitting(true);
    try {
      const sprint = await createSprint(selectedProjectId, sprintGoal.trim());
      // Auto-execute the sprint
      await executeSprint(sprint.sprint_id);
      setSprintGoal('');
      setShowNewSprint(false);
      navigate(`/sprints/${sprint.sprint_id}`);
    } catch {
      // Could show error toast
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowNewProject(true)}
            className="px-3 py-1.5 text-sm rounded bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700"
          >
            New Project
          </button>
          {projects.length > 0 && (
            <button
              onClick={() => setShowNewSprint(true)}
              className="px-3 py-1.5 text-sm rounded bg-blue-600 text-white hover:bg-blue-700"
            >
              New Sprint
            </button>
          )}
        </div>
      </div>

      {/* New Project Form */}
      {showNewProject && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border p-4 mb-6 shadow-sm">
          <h3 className="font-semibold mb-3">Create Project</h3>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Project name"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCreateProject()}
              className="flex-1 px-3 py-1.5 text-sm rounded border border-gray-300 dark:border-gray-700 bg-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
            <button
              onClick={handleCreateProject}
              disabled={submitting || !projectName.trim()}
              className="px-4 py-1.5 text-sm rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting ? 'Creating...' : 'Create'}
            </button>
            <button
              onClick={() => { setShowNewProject(false); setProjectName(''); }}
              className="px-3 py-1.5 text-sm rounded bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* New Sprint Form */}
      {showNewSprint && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border p-4 mb-6 shadow-sm">
          <h3 className="font-semibold mb-3">Start a Sprint</h3>
          <p className="text-sm text-gray-500 mb-3">
            Describe what you want the AI team to build. The PM agent will decompose it into tasks.
          </p>
          <textarea
            placeholder='e.g. "Build a REST API for a todo app with authentication"'
            value={sprintGoal}
            onChange={(e) => setSprintGoal(e.target.value)}
            className="w-full px-3 py-2 text-sm rounded border border-gray-300 dark:border-gray-700 bg-transparent focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            rows={3}
            autoFocus
          />
          <div className="flex justify-end gap-2 mt-3">
            <button
              onClick={() => { setShowNewSprint(false); setSprintGoal(''); }}
              className="px-3 py-1.5 text-sm rounded bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700"
            >
              Cancel
            </button>
            <button
              onClick={handleStartSprint}
              disabled={submitting || !sprintGoal.trim()}
              className="px-4 py-1.5 text-sm rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting ? 'Starting...' : 'Start Sprint'}
            </button>
          </div>
        </div>
      )}

      {projects.length === 0 && !showNewProject ? (
        <div className="text-center py-16">
          <p className="text-5xl mb-4">🚀</p>
          <h2 className="text-xl font-semibold mb-2">Welcome to FoundrAI</h2>
          <p className="text-gray-500 mb-4">
            Create your first project to get started with your AI founding team.
          </p>
          <button
            onClick={() => setShowNewProject(true)}
            className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700"
          >
            Create Project
          </button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            {projects.map((p) => (
              <button
                key={p.project_id}
                onClick={() => setSelectedProjectId(p.project_id)}
                className={`text-left bg-white dark:bg-gray-800 rounded-lg border p-4 shadow-sm transition-shadow hover:shadow-md ${
                  selectedProjectId === p.project_id
                    ? 'ring-2 ring-blue-500'
                    : ''
                }`}
              >
                <h3 className="font-semibold">{p.name}</h3>
                <p className="text-sm text-gray-500 mt-1">{p.description || 'No description'}</p>
                <p className="text-xs text-gray-400 mt-2">{p.sprint_count} sprint{p.sprint_count !== 1 ? 's' : ''}</p>
              </button>
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

          {recentSprints.length === 0 && !showNewSprint && (
            <div className="text-center py-8 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
              <p className="text-gray-500 mb-3">No sprints yet for this project.</p>
              <button
                onClick={() => setShowNewSprint(true)}
                className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700"
              >
                Start First Sprint
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
