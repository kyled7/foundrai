import { DollarSign } from 'lucide-react';

interface BudgetConfigPanelProps {
  onSave?: (config: any) => void;
  isSaving?: boolean;
}

export function BudgetConfigPanel({ onSave, isSaving }: BudgetConfigPanelProps) {
  return (
    <div role="tabpanel" id="panel-budget" className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium text-foreground">Budget Configuration</h3>
          <p className="text-xs text-muted mt-1">Configure spending limits and model tier-down behavior</p>
        </div>
      </div>

      {/* Placeholder content - will be implemented in subsequent subtasks */}
      <div className="border border-border rounded-lg p-6">
        <div className="flex items-center gap-3 text-muted">
          <DollarSign size={24} className="text-muted" />
          <p className="text-sm">
            Budget configuration interface coming soon...
          </p>
        </div>
      </div>
    </div>
  );
}
