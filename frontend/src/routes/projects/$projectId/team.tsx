import { useState, useMemo } from 'react';
import { useParams } from '@tanstack/react-router';
import { useAgents, useUpdateAgent } from '@/hooks/use-agents';
import { useRecommendations, useCostSavings } from '@/hooks/use-recommendations';
import { AgentAvatar } from '@/components/shared/AgentAvatar';
import { PageSkeleton } from '@/components/shared/LoadingSkeleton';
import { EmptyState } from '@/components/shared/EmptyState';
import { ModelRecommendationCard } from '@/components/team/ModelRecommendationCard';
import { CostSavingsEstimate } from '@/components/team/CostSavingsEstimate';
import { cn } from '@/lib/utils';
import { Save, ChevronDown, ChevronUp } from 'lucide-react';
import { toast } from 'sonner';
import type { AutonomyLevel, ModelRecommendation } from '@/lib/types';

const modelOptions = ['claude-sonnet-4', 'claude-opus-4', 'gpt-4o', 'gpt-4o-mini'];
const autonomyLevels: AutonomyLevel[] = ['low', 'medium', 'high'];

export function TeamConfigPage() {
  const { projectId } = useParams({ strict: false }) as { projectId: string };
  const { data, isLoading } = useAgents(projectId);
  const updateAgent = useUpdateAgent(projectId);
  const { data: recommendations, isLoading: recommendationsLoading } = useRecommendations(projectId);
  const costSavingsMutation = useCostSavings(projectId);
  const [expandedRole, setExpandedRole] = useState<string | null>(null);
  const [localEdits, setLocalEdits] = useState<Record<string, { model?: string; autonomy_level?: AutonomyLevel; enabled?: boolean }>>({});
  const [dismissedRecommendations, setDismissedRecommendations] = useState<Set<string>>(new Set());

  // Calculate cost savings when agents and recommendations are available
  useMemo(() => {
    if (!data?.agents || !recommendations?.recommendations) return null;

    const currentConfig: Record<string, string> = {};
    const recommendedConfig: Record<string, string> = {};

    data.agents.forEach((agent) => {
      currentConfig[agent.agent_role] = agent.model;
    });

    recommendations.recommendations.forEach((rec) => {
      if (rec.recommended_model !== rec.current_model) {
        recommendedConfig[rec.agent_role] = rec.recommended_model;
      }
    });

    // Only calculate if there are actual recommendations
    if (Object.keys(recommendedConfig).length > 0) {
      costSavingsMutation.mutate({ current_config: currentConfig, recommended_config: recommendedConfig });
    }

    return null;
  }, [data?.agents, recommendations?.recommendations, costSavingsMutation]);

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

  const handleAcceptRecommendation = (recommendation: ModelRecommendation) => {
    // Apply the recommended model to the agent
    setEdit(recommendation.agent_role, 'model', recommendation.recommended_model);
    toast.success('Recommendation applied', {
      description: `${recommendation.agent_role} model set to ${recommendation.recommended_model}`,
    });
    // Remove from dismissed list if it was there
    setDismissedRecommendations((prev) => {
      const next = new Set(prev);
      next.delete(recommendation.agent_role);
      return next;
    });
  };

  const handleDismissRecommendation = (recommendation: ModelRecommendation) => {
    setDismissedRecommendations((prev) => new Set(prev).add(recommendation.agent_role));
    toast.info('Recommendation dismissed', {
      description: `You can still manually change ${recommendation.agent_role}'s model`,
    });
  };

  // Filter recommendations to show only those that aren't dismissed and have different models
  const activeRecommendations = recommendations?.recommendations?.filter(
    (rec) => !dismissedRecommendations.has(rec.agent_role) && rec.recommended_model !== rec.current_model
  ) || [];

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

      {/* Cost Savings Estimate */}
      {costSavingsMutation.data && (
        <CostSavingsEstimate
          estimate={costSavingsMutation.data}
          loading={costSavingsMutation.isPending}
        />
      )}

      {/* Recommendations Section */}
      {activeRecommendations.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">Model Recommendations</h2>
            <span className="text-xs text-muted">
              {activeRecommendations.length} recommendation{activeRecommendations.length !== 1 ? 's' : ''}
            </span>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {activeRecommendations.map((rec) => (
              <ModelRecommendationCard
                key={rec.agent_role}
                recommendation={rec}
                loading={recommendationsLoading}
                onAccept={handleAcceptRecommendation}
                onDismiss={handleDismissRecommendation}
              />
            ))}
          </div>
        </div>
      )}

      {/* Agent Configuration */}
      <div>
        <h2 className="text-lg font-semibold text-foreground mb-3">Agent Configuration</h2>
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
    </div>
  );
}
