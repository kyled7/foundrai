import { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import type { GlobalSettings, AutonomyLevel } from '@/lib/types';

interface GeneralSettingsPanelProps {
  settings: GlobalSettings;
  onSave: (updates: Partial<GlobalSettings>) => void;
  isSaving: boolean;
}

const models = [
  { group: 'Anthropic', options: ['claude-sonnet-4-20250514', 'claude-3-5-haiku-20241022'] },
  { group: 'OpenAI', options: ['gpt-4o', 'gpt-4o-mini'] },
];

const autonomyOptions: { value: AutonomyLevel; label: string; description: string }[] = [
  { value: 'low', label: 'Low', description: 'Approve everything before execution' },
  { value: 'medium', label: 'Medium', description: 'Approve risky actions only' },
  { value: 'high', label: 'High', description: 'Fully autonomous execution' },
];

export function GeneralSettingsPanel({ settings, onSave, isSaving }: GeneralSettingsPanelProps) {
  const [model, setModel] = useState(settings.default_model);
  const [autonomy, setAutonomy] = useState(settings.default_autonomy);
  const [sprintBudget, setSprintBudget] = useState(settings.budget_per_sprint_usd?.toString() ?? '');
  const [monthlyBudget, setMonthlyBudget] = useState(settings.budget_monthly_usd?.toString() ?? '');

  useEffect(() => {
    setModel(settings.default_model);
    setAutonomy(settings.default_autonomy);
    setSprintBudget(settings.budget_per_sprint_usd?.toString() ?? '');
    setMonthlyBudget(settings.budget_monthly_usd?.toString() ?? '');
  }, [settings]);

  const hasChanges =
    model !== settings.default_model ||
    autonomy !== settings.default_autonomy ||
    sprintBudget !== (settings.budget_per_sprint_usd?.toString() ?? '') ||
    monthlyBudget !== (settings.budget_monthly_usd?.toString() ?? '');

  function handleSave() {
    onSave({
      default_model: model,
      default_autonomy: autonomy,
      budget_per_sprint_usd: sprintBudget ? parseFloat(sprintBudget) : null,
      budget_monthly_usd: monthlyBudget ? parseFloat(monthlyBudget) : null,
    });
  }

  return (
    <div role="tabpanel" id="panel-general" className="space-y-8">
      {/* Default Model */}
      <fieldset className="space-y-2">
        <label htmlFor="default-model" className="block text-sm font-medium text-foreground">
          Default Model
        </label>
        <select
          id="default-model"
          value={model}
          onChange={(e) => setModel(e.target.value)}
          className="w-full max-w-md px-3 py-2 bg-background border border-border rounded-md text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        >
          {models.map((g) => (
            <optgroup key={g.group} label={g.group}>
              {g.options.map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </optgroup>
          ))}
        </select>
      </fieldset>

      {/* Autonomy Level */}
      <fieldset className="space-y-3">
        <legend className="text-sm font-medium text-foreground">Default Autonomy Level</legend>
        {autonomyOptions.map((opt) => (
          <label key={opt.value} className="flex items-start gap-3 cursor-pointer">
            <input
              type="radio"
              name="autonomy"
              value={opt.value}
              checked={autonomy === opt.value}
              onChange={() => setAutonomy(opt.value)}
              className="mt-1 accent-primary"
            />
            <div>
              <span className="text-sm font-medium text-foreground">{opt.label}</span>
              <p className="text-xs text-muted">{opt.description}</p>
            </div>
          </label>
        ))}
      </fieldset>

      {/* Budget Limits */}
      <fieldset className="space-y-4">
        <legend className="text-sm font-medium text-foreground">Budget Limits</legend>
        <div className="flex flex-col sm:flex-row gap-4 max-w-md">
          <div className="flex-1 space-y-1">
            <label htmlFor="sprint-budget" className="text-xs text-muted">Per Sprint (USD)</label>
            <input
              id="sprint-budget"
              type="number"
              min="0"
              step="0.01"
              value={sprintBudget}
              onChange={(e) => setSprintBudget(e.target.value)}
              placeholder="No limit"
              className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div className="flex-1 space-y-1">
            <label htmlFor="monthly-budget" className="text-xs text-muted">Monthly (USD)</label>
            <input
              id="monthly-budget"
              type="number"
              min="0"
              step="0.01"
              value={monthlyBudget}
              onChange={(e) => setMonthlyBudget(e.target.value)}
              placeholder="No limit"
              className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>
      </fieldset>

      <button
        onClick={handleSave}
        disabled={!hasChanges || isSaving}
        className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isSaving && <Loader2 size={14} className="animate-spin" />}
        Save Changes
      </button>
    </div>
  );
}
