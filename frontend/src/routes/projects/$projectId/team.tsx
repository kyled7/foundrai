import { useState } from 'react';
import { useParams } from '@tanstack/react-router';
import { useAgents, useUpdateAgent } from '@/hooks/use-agents';
import { AgentAvatar } from '@/components/shared/AgentAvatar';
import { PageSkeleton } from '@/components/shared/LoadingSkeleton';
import { EmptyState } from '@/components/shared/EmptyState';
import { cn } from '@/lib/utils';
import { Save, ChevronDown, ChevronUp } from 'lucide-react';
import type { AutonomyLevel } from '@/lib/types';

const modelOptions = ['claude-sonnet-4', 'claude-opus-4', 'gpt-4o', 'gpt-4o-mini'];
const autonomyLevels: AutonomyLevel[] = ['low', 'medium', 'high'];

export function TeamConfigPage() {
  const { projectId } = useParams({ strict: false }) as { projectId: string };
  const { data, isLoading } = useAgents(projectId);
  const updateAgent = useUpdateAgent(projectId);
  const [expandedRole, setExpandedRole] = useState<string | null>(null);
  const [localEdits, setLocalEdits] = useState<Record<string, { model?: string; autonomy_level?: AutonomyLevel; enabled?: boolean }>>({});

  if (isLoading) return <PageSkeleton />;
  if (!data?.agents?.length) {
    return (
      <div className="p-6">
        <EmptyState title="No agents configured" description="Create a project first to configure agents." />
      </div>
    );
  }

  const handleSave = (role: string) => {
    const edits = localEdits[role];
    if (!edits) return;
    updateAgent.mutate({ role, data: edits });
    setLocalEdits((prev) => { const next = { ...prev }; delete next[role]; return next; });
  };

  const setEdit = (role: string, field: string, value: string | boolean) => {
    setLocalEdits((prev) => ({
      ...prev,
      [role]: { ...prev[role], [field]: value },
    }));
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Team Configuration</h1>
          <p className="text-muted text-sm mt-1">Configure your AI team members</p>
        </div>
        <a href={`/projects/${projectId}`} className="text-sm text-muted hover:text-foreground">
          ← Back to Project
        </a>
      </div>

      <div className="space-y-3">
        {data.agents.map((agent) => {
          const edits = localEdits[agent.agent_role];
          const isExpanded = expandedRole === agent.agent_role;
          const hasChanges = !!edits;
          const currentModel = edits?.model ?? agent.model;
          const currentAutonomy = edits?.autonomy_level ?? agent.autonomy_level;
          const currentEnabled = edits?.enabled ?? agent.enabled;

          return (
            <div key={agent.agent_role} className="bg-card border border-border rounded-lg overflow-hidden">
              {/* Header */}
              <div
                className="flex items-center gap-3 p-4 cursor-pointer hover:bg-border/30"
                onClick={() => setExpandedRole(isExpanded ? null : agent.agent_role)}
              >
                <AgentAvatar role={agent.agent_role} />
                <div className="flex-1">
                  <p className="text-foreground font-medium capitalize">{agent.agent_role.replace('_', ' ')}</p>
                  <p className="text-muted text-xs">{currentModel} · {currentAutonomy} autonomy</p>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); setEdit(agent.agent_role, 'enabled', !currentEnabled); }}
                  className={cn(
                    'px-3 py-1 rounded-full text-xs font-medium transition-colors',
                    currentEnabled ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'
                  )}
                >
                  {currentEnabled ? 'Enabled' : 'Disabled'}
                </button>
                {isExpanded ? <ChevronUp size={16} className="text-muted" /> : <ChevronDown size={16} className="text-muted" />}
              </div>

              {/* Expanded config */}
              {isExpanded && (
                <div className="px-4 pb-4 space-y-4 border-t border-border pt-4">
                  {/* Model */}
                  <div>
                    <label className="text-sm text-muted block mb-1">Model</label>
                    <select
                      value={currentModel}
                      onChange={(e) => setEdit(agent.agent_role, 'model', e.target.value)}
                      className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm text-foreground"
                    >
                      {modelOptions.map((m) => <option key={m} value={m}>{m}</option>)}
                    </select>
                  </div>

                  {/* Autonomy */}
                  <div>
                    <label className="text-sm text-muted block mb-1">Autonomy Level</label>
                    <div className="flex gap-2">
                      {autonomyLevels.map((level) => (
                        <button
                          key={level}
                          onClick={() => setEdit(agent.agent_role, 'autonomy_level', level)}
                          className={cn(
                            'px-3 py-1.5 rounded-md text-sm capitalize border transition-colors',
                            currentAutonomy === level
                              ? 'border-primary bg-primary/10 text-primary'
                              : 'border-border text-muted hover:text-foreground'
                          )}
                        >
                          {level}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Save */}
                  {hasChanges && (
                    <button
                      onClick={() => handleSave(agent.agent_role)}
                      disabled={updateAgent.isPending}
                      className="flex items-center gap-1.5 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50"
                    >
                      <Save size={14} />
                      {updateAgent.isPending ? 'Saving...' : 'Save Changes'}
                    </button>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
