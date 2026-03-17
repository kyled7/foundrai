import { useState } from 'react';
import { useParams } from '@tanstack/react-router';
import { useProject } from '@/hooks/use-projects';
import { useSprints } from '@/hooks/use-sprints';
import { useAgents } from '@/hooks/use-agents';
import { useLearnings } from '@/hooks/use-analytics';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { AgentAvatar } from '@/components/shared/AgentAvatar';
import { TimeAgo } from '@/components/shared/TimeAgo';
import { EmptyState } from '@/components/shared/EmptyState';
import { PageSkeleton } from '@/components/shared/LoadingSkeleton';
import { cn } from '@/lib/utils';
import { Play } from 'lucide-react';

const tabs = ['sprints', 'team', 'learnings'] as const;
type Tab = typeof tabs[number];

export function ProjectDetailPage() {
  const { projectId } = useParams({ strict: false }) as { projectId: string };
  const [activeTab, setActiveTab] = useState<Tab>('sprints');
  const { data: project, isLoading } = useProject(projectId);
  const { data: sprintsData } = useSprints(projectId);
  const { data: agentsData } = useAgents(projectId);
  const { data: learningsData } = useLearnings(projectId);

  if (isLoading || !project) return <PageSkeleton />;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">{project.name}</h1>
        {project.description && <p className="text-muted mt-1">{project.description}</p>}
      </div>

      {/* Tabs */}
      <div className="border-b border-border">
        <nav className="flex gap-6">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                'pb-3 text-sm font-medium capitalize border-b-2 transition-colors',
                activeTab === tab
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted hover:text-foreground'
              )}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      {activeTab === 'sprints' && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">Sprints</h2>
            <a
              href={`/projects/${projectId}/sprint`}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90"
            >
              <Play size={14} />
              New Sprint
            </a>
          </div>
          {!sprintsData?.sprints?.length ? (
            <EmptyState title="No sprints yet" description="Start your first sprint to see your AI team in action." />
          ) : (
            <div className="space-y-2">
              {sprintsData.sprints.map((s) => (
                <div key={s.sprint_id} className="bg-card border border-border rounded-lg p-4 flex items-center gap-4">
                  <span className="text-muted text-sm font-mono">#{s.sprint_number}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-foreground text-sm truncate">{s.goal}</p>
                  </div>
                  <StatusBadge status={s.status} />
                  <span className="text-muted text-xs">
                    <TimeAgo timestamp={s.created_at} />
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'team' && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">Team</h2>
            <a
              href={`/projects/${projectId}/team`}
              className="px-3 py-1.5 border border-border rounded-md text-sm text-muted hover:text-foreground"
            >
              Configure
            </a>
          </div>
          {!agentsData?.agents?.length ? (
            <EmptyState title="No agents configured" description="Configure your team to get started." />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {agentsData.agents.map((a) => (
                <div key={a.agent_role} className="bg-card border border-border rounded-lg p-4 flex items-center gap-3">
                  <AgentAvatar role={a.agent_role} />
                  <div>
                    <p className="text-foreground text-sm font-medium capitalize">{a.agent_role.replace('_', ' ')}</p>
                    <p className="text-muted text-xs">{a.model}</p>
                  </div>
                  <span className={cn('ml-auto text-xs px-2 py-0.5 rounded-full', a.enabled ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400')}>
                    {a.enabled ? 'Active' : 'Disabled'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'learnings' && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground">Learnings</h2>
          {!learningsData?.learnings?.length ? (
            <EmptyState title="No learnings yet" description="Learnings are generated after sprint retrospectives." />
          ) : (
            <div className="space-y-2">
              {learningsData.learnings.map((l) => (
                <div key={l.learning_id} className="bg-card border border-border rounded-lg p-4">
                  <p className="text-foreground text-sm">{l.content}</p>
                  <div className="flex gap-2 mt-2">
                    <span className="text-xs px-2 py-0.5 bg-primary/10 text-primary rounded-full">{l.category}</span>
                    <span className="text-muted text-xs">
                      <TimeAgo timestamp={l.created_at} />
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
