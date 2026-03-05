import type { Project, Sprint } from '@/lib/types';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { CostDisplay } from '@/components/shared/CostDisplay';
import { TimeAgo } from '@/components/shared/TimeAgo';
import { Users, Play, Eye } from 'lucide-react';

interface ProjectCardProps {
  project: Project;
  lastSprint?: Sprint | null;
  agentCount?: number;
  totalCost?: number;
}

export function ProjectCard({ project, lastSprint, agentCount = 0, totalCost = 0 }: ProjectCardProps) {
  const hasActiveSprint = !!project.current_sprint_id;

  return (
    <a
      href={`/projects/${project.project_id}`}
      className="bg-card border border-border rounded-lg p-4 hover:border-primary/50 transition-colors block"
    >
      <div className="flex items-start justify-between">
        <h3 className="font-semibold text-foreground truncate">{project.name}</h3>
        {lastSprint && <StatusBadge status={lastSprint.status} />}
      </div>

      {project.description && (
        <p className="text-muted text-sm mt-1 line-clamp-2">{project.description}</p>
      )}

      {lastSprint && (
        <p className="text-muted text-xs mt-2 truncate">
          Sprint #{lastSprint.sprint_number}: {lastSprint.goal}
        </p>
      )}

      <div className="flex items-center gap-3 mt-3 text-sm text-muted">
        <span className="flex items-center gap-1">
          <Users size={14} />
          {agentCount}
        </span>
        <span>{project.sprint_count} sprints</span>
        {totalCost > 0 && <CostDisplay costUsd={totalCost} className="text-xs" />}
        <TimeAgo date={project.created_at} className="text-xs ml-auto" />
      </div>

      <div className="mt-3 pt-3 border-t border-border">
        <button
          onClick={(e) => {
            e.preventDefault();
            window.location.href = hasActiveSprint
              ? `/projects/${project.project_id}/sprint`
              : `/projects/${project.project_id}?tab=sprints`;
          }}
          className="flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary/80"
        >
          {hasActiveSprint ? <Eye size={14} /> : <Play size={14} />}
          {hasActiveSprint ? 'View Sprint' : 'Start Sprint'}
        </button>
      </div>
    </a>
  );
}
