import { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';

interface BudgetConfig {
  sprint_budget_usd: number | null;
  per_agent_budgets: Record<string, number | null>;
  warning_threshold_percent: number;
}

interface BudgetConfigPanelProps {
  config?: BudgetConfig;
  onSave?: (config: BudgetConfig) => void;
  isSaving?: boolean;
}

const agentRoles = [
  { value: 'product_manager', label: 'Product Manager' },
  { value: 'developer', label: 'Developer' },
  { value: 'qa_engineer', label: 'QA Engineer' },
  { value: 'architect', label: 'Architect' },
  { value: 'designer', label: 'Designer' },
  { value: 'devops', label: 'DevOps' },
];

export function BudgetConfigPanel({ config, onSave, isSaving }: BudgetConfigPanelProps) {
  const [sprintBudget, setSprintBudget] = useState(config?.sprint_budget_usd?.toString() ?? '');
  const [warningThreshold, setWarningThreshold] = useState(config?.warning_threshold_percent?.toString() ?? '80');
  const [agentBudgets, setAgentBudgets] = useState<Record<string, string>>(() => {
    const initial: Record<string, string> = {};
    agentRoles.forEach(({ value }) => {
      initial[value] = config?.per_agent_budgets?.[value]?.toString() ?? '';
    });
    return initial;
  });

  useEffect(() => {
    setSprintBudget(config?.sprint_budget_usd?.toString() ?? '');
    setWarningThreshold(config?.warning_threshold_percent?.toString() ?? '80');
    const updated: Record<string, string> = {};
    agentRoles.forEach(({ value }) => {
      updated[value] = config?.per_agent_budgets?.[value]?.toString() ?? '';
    });
    setAgentBudgets(updated);
  }, [config]);

  const hasChanges =
    sprintBudget !== (config?.sprint_budget_usd?.toString() ?? '') ||
    warningThreshold !== (config?.warning_threshold_percent?.toString() ?? '80') ||
    agentRoles.some(({ value }) => agentBudgets[value] !== (config?.per_agent_budgets?.[value]?.toString() ?? ''));

  function handleSave() {
    if (!onSave) return;

    const per_agent_budgets: Record<string, number | null> = {};
    agentRoles.forEach(({ value }) => {
      per_agent_budgets[value] = agentBudgets[value] ? parseFloat(agentBudgets[value]) : null;
    });

    onSave({
      sprint_budget_usd: sprintBudget ? parseFloat(sprintBudget) : null,
      per_agent_budgets,
      warning_threshold_percent: parseFloat(warningThreshold),
    });
  }

  function handleAgentBudgetChange(role: string, value: string) {
    setAgentBudgets(prev => ({ ...prev, [role]: value }));
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

      <button
        onClick={handleSave}
        disabled={!hasChanges || isSaving || !onSave}
        className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isSaving && <Loader2 size={14} className="animate-spin" />}
        Save Changes
      </button>
    </div>
  );
}
