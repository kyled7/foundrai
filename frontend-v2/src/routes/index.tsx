import { useProjects } from '@/hooks/use-projects';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { EmptyState } from '@/components/shared/EmptyState';
import { PageSkeleton } from '@/components/shared/LoadingSkeleton';
import { TimeAgo } from '@/components/shared/TimeAgo';
import { Link } from '@tanstack/react-router';
import { Plus } from 'lucide-react';

export function DashboardPage() {
  const { data, isLoading, error } = useProjects();

  if (isLoading) return <PageSkeleton />;
  if (error) return <div className="p-6 text-red-400">Failed to load projects</div>;

  const projects = data?.projects ?? [];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
        <Link
          to="/projects/new"
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90"
        >
          <Plus size={16} />
          New Project
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <p className="text-muted text-sm">Projects</p>
          <p className="text-2xl font-bold text-foreground">{projects.length}</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <p className="text-muted text-sm">Active Sprints</p>
          <p className="text-2xl font-bold text-foreground">
            {projects.filter(p => p.current_sprint_id).length}
          </p>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <p className="text-muted text-sm">Total Sprints</p>
          <p className="text-2xl font-bold text-foreground">
            {projects.reduce((sum, p) => sum + p.sprint_count, 0)}
          </p>
        </div>
      </div>

      {/* Project list */}
      {projects.length === 0 ? (
        <EmptyState
          icon="🚀"
          title="No projects yet"
          description="Create your first project to get started with FoundrAI."
          action={
            <Link
              to="/projects/new"
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90"
            >
              Create Project
            </Link>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project) => (
            <a
              key={project.project_id}
              href={`/projects/${project.project_id}`}
              className="bg-card border border-border rounded-lg p-4 hover:border-primary/50 transition-colors"
            >
              <h3 className="font-semibold text-foreground">{project.name}</h3>
              {project.description && (
                <p className="text-muted text-sm mt-1 line-clamp-2">{project.description}</p>
              )}
              <div className="flex items-center gap-3 mt-3 text-sm">
                <span className="text-muted">{project.sprint_count} sprints</span>
                {project.current_sprint_id && <StatusBadge status="in_progress" />}
                <TimeAgo date={project.created_at} className="text-muted text-xs ml-auto" />
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
