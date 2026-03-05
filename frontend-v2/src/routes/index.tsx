import { useDashboardStats } from '@/hooks/use-dashboard-stats';
import { StatCard } from '@/components/dashboard/StatCard';
import { ProjectCard } from '@/components/dashboard/ProjectCard';
import { EmptyState } from '@/components/shared/EmptyState';
import { PageSkeleton } from '@/components/shared/LoadingSkeleton';
import { GlobalStats } from '@/components/analytics/GlobalStats';
import { Link } from '@tanstack/react-router';
import { Plus, FolderKanban, Zap, DollarSign, BarChart3 } from 'lucide-react';

export function DashboardPage() {
  const { projects, stats, isLoading } = useDashboardStats();

  if (isLoading) return <PageSkeleton />;

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

      {/* Global Analytics */}
      <GlobalStats />

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Projects" value={stats.totalProjects} icon={<FolderKanban size={18} />} />
        <StatCard label="Active Sprints" value={stats.activeSprints} icon={<Zap size={18} />} />
        <StatCard label="Total Sprints" value={stats.totalSprints} icon={<BarChart3 size={18} />} />
        <StatCard label="Total Cost" value={`$${stats.totalCost.toFixed(2)}`} icon={<DollarSign size={18} />} />
      </div>

      {/* Project list */}
      {stats.totalProjects === 0 ? (
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
          {projects.map((q, i) => {
            const data = q.data;
            if (!data) return null;
            return (
              <ProjectCard
                key={data.project.project_id ?? i}
                project={data.project}
                lastSprint={data.lastSprint}
                agentCount={data.agentCount}
                totalCost={data.totalCost}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
