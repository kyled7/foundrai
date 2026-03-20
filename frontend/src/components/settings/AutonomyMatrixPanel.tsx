import { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import type { ActionType, AutonomyMode } from '@/lib/types';

interface AutonomyMatrixPanelProps {
  projectId: string;
}

// Agent roles in the system
const agentRoles = [
  'ProductManager',
  'Developer',
  'QAEngineer',
  'Architect',
  'Designer',
  'DevOps',
];

// Action types with display labels
const actionTypes: { value: ActionType; label: string }[] = [
  { value: 'code_write', label: 'Code Write' },
  { value: 'code_execute', label: 'Code Execute' },
  { value: 'file_create', label: 'File Create' },
  { value: 'file_modify', label: 'File Modify' },
  { value: 'file_delete', label: 'File Delete' },
  { value: 'git_commit', label: 'Git Commit' },
  { value: 'git_push', label: 'Git Push' },
  { value: 'api_call', label: 'API Call' },
  { value: 'tool_use', label: 'Tool Use' },
  { value: 'task_create', label: 'Task Create' },
  { value: 'task_assign', label: 'Task Assign' },
  { value: 'message_send', label: 'Message Send' },
  { value: 'code_review', label: 'Code Review' },
  { value: 'deployment', label: 'Deployment' },
];

// Autonomy mode options
const autonomyModes: { value: AutonomyMode; label: string; color: string }[] = [
  { value: 'auto_approve', label: 'Auto-Approve', color: 'text-green-600 dark:text-green-400' },
  { value: 'notify', label: 'Notify', color: 'text-blue-600 dark:text-blue-400' },
  { value: 'require_approval', label: 'Require Approval', color: 'text-yellow-600 dark:text-yellow-400' },
  { value: 'block', label: 'Block', color: 'text-red-600 dark:text-red-400' },
];

export function AutonomyMatrixPanel({ projectId }: AutonomyMatrixPanelProps) {
  const [matrix, setMatrix] = useState<Record<string, Record<ActionType, AutonomyMode>>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  // Load configuration on mount
  useEffect(() => {
    loadConfig();
  }, [projectId]);

  async function loadConfig() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/projects/${projectId}/autonomy/config`);
      if (!response.ok) {
        throw new Error('Failed to load autonomy configuration');
      }
      const data = await response.json();
      setMatrix(data.matrix || {});
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load configuration');
      console.error('Failed to load autonomy config:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const response = await fetch(`/api/projects/${projectId}/autonomy/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ matrix }),
      });
      if (!response.ok) {
        throw new Error('Failed to save autonomy configuration');
      }
      const data = await response.json();
      setMatrix(data.matrix);
      setHasChanges(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save configuration');
      console.error('Failed to save autonomy config:', err);
    } finally {
      setSaving(false);
    }
  }

  function handleCellChange(agentRole: string, actionType: ActionType, mode: AutonomyMode) {
    setMatrix((prev) => {
      const updated = { ...prev };
      if (!updated[agentRole]) {
        updated[agentRole] = {} as Record<ActionType, AutonomyMode>;
      }
      updated[agentRole] = {
        ...updated[agentRole],
        [actionType]: mode,
      };
      return updated;
    });
    setHasChanges(true);
  }

  function getCellValue(agentRole: string, actionType: ActionType): AutonomyMode {
    return matrix[agentRole]?.[actionType] || 'notify';
  }

  function getModeColor(mode: AutonomyMode): string {
    return autonomyModes.find((m) => m.value === mode)?.color || 'text-foreground';
  }

  if (loading) {
    return (
      <div role="tabpanel" id="panel-autonomy" className="flex items-center justify-center py-12">
        <Loader2 className="animate-spin text-muted" size={24} />
      </div>
    );
  }

  return (
    <div role="tabpanel" id="panel-autonomy" className="space-y-6">
      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md text-sm text-red-800 dark:text-red-200">
          {error}
        </div>
      )}

      <div>
        <h2 className="text-lg font-semibold text-foreground mb-2">Autonomy Matrix</h2>
        <p className="text-sm text-muted mb-4">
          Configure approval policies for each agent-action combination. Changes take effect immediately.
        </p>
      </div>

      {/* Matrix Grid */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr>
              <th className="sticky left-0 z-10 bg-background border border-border p-2 text-left font-medium text-foreground min-w-[120px]">
                Agent / Action
              </th>
              {actionTypes.map((action) => (
                <th
                  key={action.value}
                  className="border border-border p-2 text-left font-medium text-foreground min-w-[140px]"
                >
                  {action.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {agentRoles.map((role) => (
              <tr key={role}>
                <td className="sticky left-0 z-10 bg-background border border-border p-2 font-medium text-foreground">
                  {role}
                </td>
                {actionTypes.map((action) => {
                  const currentMode = getCellValue(role, action.value);
                  return (
                    <td key={action.value} className="border border-border p-2">
                      <select
                        value={currentMode}
                        onChange={(e) => handleCellChange(role, action.value, e.target.value as AutonomyMode)}
                        className={`w-full px-2 py-1.5 bg-background border border-border rounded text-xs focus:outline-none focus:ring-2 focus:ring-primary ${getModeColor(currentMode)}`}
                      >
                        {autonomyModes.map((mode) => (
                          <option key={mode.value} value={mode.value}>
                            {mode.label}
                          </option>
                        ))}
                      </select>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Save Button */}
      <button
        onClick={handleSave}
        disabled={!hasChanges || saving}
        className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {saving && <Loader2 size={14} className="animate-spin" />}
        Save Changes
      </button>
    </div>
  );
}
