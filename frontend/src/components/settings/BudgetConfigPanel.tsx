import { useState, useEffect } from 'react';
import { Loader2, Plus, X } from 'lucide-react';
import { useBudgetConfig, useSaveBudgetConfig } from '@/hooks/use-budget-config';

const agentRoles = [
  { value: 'product_manager', label: 'Product Manager' },
  { value: 'developer', label: 'Developer' },
  { value: 'qa_engineer', label: 'QA Engineer' },
  { value: 'architect', label: 'Architect' },
  { value: 'designer', label: 'Designer' },
  { value: 'devops', label: 'DevOps' },
];

export function BudgetConfigPanel() {
  const { data: config, isLoading } = useBudgetConfig();
  const saveBudgetConfig = useSaveBudgetConfig();
  const [sprintBudget, setSprintBudget] = useState(config?.sprint_budget_usd?.toString() ?? '');
  const [warningThreshold, setWarningThreshold] = useState(config?.warning_threshold_percent?.toString() ?? '80');
  const [agentBudgets, setAgentBudgets] = useState<Record<string, string>>(() => {
    const initial: Record<string, string> = {};
    agentRoles.forEach(({ value }) => {
      initial[value] = config?.per_agent_budgets?.[value]?.toString() ?? '';
    });
    return initial;
  });
  const [tierDownMappings, setTierDownMappings] = useState<Record<string, string>>(() =>
    config?.model_tier_down_mapping ?? {}
  );
  const [newSourceModel, setNewSourceModel] = useState('');
  const [newFallbackModel, setNewFallbackModel] = useState('');
  const [showAddMapping, setShowAddMapping] = useState(false);

  useEffect(() => {
    setSprintBudget(config?.sprint_budget_usd?.toString() ?? '');
    setWarningThreshold(config?.warning_threshold_percent?.toString() ?? '80');
    const updated: Record<string, string> = {};
    agentRoles.forEach(({ value }) => {
      updated[value] = config?.per_agent_budgets?.[value]?.toString() ?? '';
    });
    setAgentBudgets(updated);
    setTierDownMappings(config?.model_tier_down_mapping ?? {});
  }, [config]);

  const hasChanges =
    sprintBudget !== (config?.sprint_budget_usd?.toString() ?? '') ||
    warningThreshold !== (config?.warning_threshold_percent?.toString() ?? '80') ||
    agentRoles.some(({ value }) => agentBudgets[value] !== (config?.per_agent_budgets?.[value]?.toString() ?? '')) ||
    JSON.stringify(tierDownMappings) !== JSON.stringify(config?.model_tier_down_mapping ?? {});

  function handleSave() {
    const per_agent_budgets: Record<string, number | null> = {};
    agentRoles.forEach(({ value }) => {
      per_agent_budgets[value] = agentBudgets[value] ? parseFloat(agentBudgets[value]) : null;
    });

    saveBudgetConfig.mutate({
      sprint_budget_usd: sprintBudget ? parseFloat(sprintBudget) : null,
      per_agent_budgets,
      warning_threshold_percent: parseFloat(warningThreshold),
      model_tier_down_mapping: tierDownMappings,
    });
  }

  function handleAgentBudgetChange(role: string, value: string) {
    setAgentBudgets(prev => ({ ...prev, [role]: value }));
  }

  function handleAddMapping() {
    if (!newSourceModel.trim() || !newFallbackModel.trim()) return;
    setTierDownMappings(prev => ({ ...prev, [newSourceModel.trim()]: newFallbackModel.trim() }));
    setNewSourceModel('');
    setNewFallbackModel('');
    setShowAddMapping(false);
  }

  function handleRemoveMapping(sourceModel: string) {
    setTierDownMappings(prev => {
      const updated = { ...prev };
      delete updated[sourceModel];
      return updated;
    });
  }

  if (isLoading) {
    return (
      <div role="tabpanel" id="panel-budget" className="flex items-center justify-center py-12">
        <Loader2 className="animate-spin text-muted" size={32} />
      </div>
    );
  }

  return (
    <div role="tabpanel" id="panel-budget" className="space-y-8">
      {/* Sprint Budget */}
      <fieldset className="space-y-2">
        <label htmlFor="sprint-budget" className="block text-sm font-medium text-foreground">
          Sprint Budget (USD)
        </label>
        <p className="text-xs text-muted mb-2">
          Maximum budget per sprint. Leave empty for no limit.
        </p>
        <input
          id="sprint-budget"
          type="number"
          min="0"
          step="0.01"
          value={sprintBudget}
          onChange={(e) => setSprintBudget(e.target.value)}
          placeholder="No limit"
          className="w-full max-w-md px-3 py-2 bg-background border border-border rounded-md text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </fieldset>

      {/* Per-Agent Budgets */}
      <fieldset className="space-y-4">
        <legend className="text-sm font-medium text-foreground">Per-Agent Budgets (USD)</legend>
        <p className="text-xs text-muted">
          Individual budget limits for each agent role. Leave empty for no limit.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-4xl">
          {agentRoles.map(({ value, label }) => (
            <div key={value} className="space-y-1">
              <label htmlFor={`agent-budget-${value}`} className="text-xs text-muted">
                {label}
              </label>
              <input
                id={`agent-budget-${value}`}
                type="number"
                min="0"
                step="0.01"
                value={agentBudgets[value]}
                onChange={(e) => handleAgentBudgetChange(value, e.target.value)}
                placeholder="No limit"
                className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          ))}
        </div>
      </fieldset>

      {/* Warning Threshold */}
      <fieldset className="space-y-2">
        <label htmlFor="warning-threshold" className="block text-sm font-medium text-foreground">
          Warning Threshold (%)
        </label>
        <p className="text-xs text-muted mb-2">
          Show warning when budget usage exceeds this percentage (1-100).
        </p>
        <input
          id="warning-threshold"
          type="number"
          min="1"
          max="100"
          step="1"
          value={warningThreshold}
          onChange={(e) => setWarningThreshold(e.target.value)}
          className="w-full max-w-md px-3 py-2 bg-background border border-border rounded-md text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </fieldset>

      {/* Model Tier-Down Mapping */}
      <fieldset className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <legend className="text-sm font-medium text-foreground">Model Tier-Down Mapping</legend>
            <p className="text-xs text-muted mt-1">
              Define fallback models when budget limits are reached
            </p>
          </div>
          <button
            onClick={() => setShowAddMapping(true)}
            className="flex items-center gap-1.5 px-3 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90"
          >
            <Plus size={14} />
            Add Mapping
          </button>
        </div>

        {Object.keys(tierDownMappings).length === 0 && !showAddMapping ? (
          <p className="text-sm text-muted py-8 text-center">No tier-down mappings configured</p>
        ) : (
          <div className="space-y-2 max-w-4xl">
            {Object.entries(tierDownMappings).map(([sourceModel, fallbackModel]) => (
              <div
                key={sourceModel}
                className="flex items-center gap-3 p-3 bg-background border border-border rounded-md"
              >
                <div className="flex-1 grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-muted mb-1">Source Model</p>
                    <p className="text-sm text-foreground font-mono">{sourceModel}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted mb-1">Fallback Model</p>
                    <p className="text-sm text-foreground font-mono">{fallbackModel}</p>
                  </div>
                </div>
                <button
                  onClick={() => handleRemoveMapping(sourceModel)}
                  className="p-2 text-muted hover:text-destructive hover:bg-destructive/10 rounded-md transition-colors"
                  aria-label="Remove mapping"
                >
                  <X size={16} />
                </button>
              </div>
            ))}

            {showAddMapping && (
              <div className="flex items-end gap-3 p-3 bg-muted/30 border border-border rounded-md">
                <div className="flex-1 grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="new-source-model" className="text-xs text-muted mb-1 block">
                      Source Model
                    </label>
                    <input
                      id="new-source-model"
                      type="text"
                      value={newSourceModel}
                      onChange={(e) => setNewSourceModel(e.target.value)}
                      placeholder="e.g., gpt-4"
                      className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary font-mono"
                    />
                  </div>
                  <div>
                    <label htmlFor="new-fallback-model" className="text-xs text-muted mb-1 block">
                      Fallback Model
                    </label>
                    <input
                      id="new-fallback-model"
                      type="text"
                      value={newFallbackModel}
                      onChange={(e) => setNewFallbackModel(e.target.value)}
                      placeholder="e.g., gpt-3.5-turbo"
                      className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary font-mono"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleAddMapping}
                    disabled={!newSourceModel.trim() || !newFallbackModel.trim()}
                    className="px-3 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Add
                  </button>
                  <button
                    onClick={() => {
                      setShowAddMapping(false);
                      setNewSourceModel('');
                      setNewFallbackModel('');
                    }}
                    className="px-3 py-2 bg-background border border-border text-foreground rounded-md text-sm font-medium hover:bg-muted"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </fieldset>

      <button
        onClick={handleSave}
        disabled={!hasChanges || saveBudgetConfig.isPending}
        className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {saveBudgetConfig.isPending && <Loader2 size={14} className="animate-spin" />}
        Save Changes
      </button>
    </div>
  );
}
