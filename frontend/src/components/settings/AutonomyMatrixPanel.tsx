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

// Preset profiles
type ProfileName = 'full_autonomy' | 'supervised' | 'manual_review' | 'custom';

interface Profile {
  value: ProfileName;
  label: string;
  description: string;
  matrix: Record<string, Record<ActionType, AutonomyMode>>;
}

function createProfileMatrix(defaultMode: AutonomyMode, overrides?: Partial<Record<ActionType, AutonomyMode>>): Record<string, Record<ActionType, AutonomyMode>> {
  const matrix: Record<string, Record<ActionType, AutonomyMode>> = {};
  agentRoles.forEach((role) => {
    matrix[role] = {} as Record<ActionType, AutonomyMode>;
    actionTypes.forEach((action) => {
      matrix[role][action.value] = overrides?.[action.value] ?? defaultMode;
    });
  });
  return matrix;
}

const profiles: Profile[] = [
  {
    value: 'full_autonomy',
    label: 'Full Autonomy',
    description: 'All actions auto-approved. Agents work independently.',
    matrix: createProfileMatrix('auto_approve'),
  },
  {
    value: 'supervised',
    label: 'Supervised',
    description: 'Most actions notify, risky actions require approval.',
    matrix: createProfileMatrix('notify', {
      code_execute: 'require_approval',
      file_delete: 'require_approval',
      git_push: 'require_approval',
      deployment: 'require_approval',
    }),
  },
  {
    value: 'manual_review',
    label: 'Manual Review',
    description: 'Most actions require approval. Maximum oversight.',
    matrix: createProfileMatrix('require_approval', {
      message_send: 'notify',
      task_create: 'notify',
      task_assign: 'notify',
    }),
  },
  {
    value: 'custom',
    label: 'Custom',
    description: 'User-defined configuration.',
    matrix: {},
  },
];

interface TrustMetric {
  agent_role: string;
  action_type: ActionType;
  success_rate: number;
  total_attempts: number;
  recommendation?: 'auto_approve' | 'notify' | 'require_approval';
}

export function AutonomyMatrixPanel({ projectId }: AutonomyMatrixPanelProps) {
  const [matrix, setMatrix] = useState<Record<string, Record<ActionType, AutonomyMode>>>({});
  const [selectedProfile, setSelectedProfile] = useState<ProfileName>('custom');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [trustMetrics, setTrustMetrics] = useState<TrustMetric[]>([]);
  const [loadingMetrics, setLoadingMetrics] = useState(false);

  // Load configuration on mount
  useEffect(() => {
    loadConfig();
    loadTrustMetrics();
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
      const loadedMatrix = data.matrix || {};
      setMatrix(loadedMatrix);
      setSelectedProfile(detectProfile(loadedMatrix));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load configuration');
    } finally {
      setLoading(false);
    }
  }

  async function loadTrustMetrics() {
    setLoadingMetrics(true);
    try {
      const response = await fetch(`/api/projects/${projectId}/autonomy/trust-metrics`);
      if (response.ok) {
        const data = await response.json();
        setTrustMetrics(data.metrics || []);
      }
    } catch (err) {
      // Silently fail - trust metrics are optional
    } finally {
      setLoadingMetrics(false);
    }
  }

  function detectProfile(currentMatrix: Record<string, Record<ActionType, AutonomyMode>>): ProfileName {
    // Check if matrix matches any preset profile
    for (const profile of profiles) {
      if (profile.value === 'custom') continue;

      let matches = true;
      for (const role of agentRoles) {
        for (const action of actionTypes) {
          const expected = profile.matrix[role]?.[action.value];
          const actual = currentMatrix[role]?.[action.value] || 'notify';
          if (expected !== actual) {
            matches = false;
            break;
          }
        }
        if (!matches) break;
      }

      if (matches) {
        return profile.value;
      }
    }

    return 'custom';
  }

  function handleProfileChange(profileName: ProfileName) {
    setSelectedProfile(profileName);

    const profile = profiles.find((p) => p.value === profileName);
    if (profile && profile.value !== 'custom') {
      setMatrix(profile.matrix);
      setHasChanges(true);
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
    setSelectedProfile('custom');
    setHasChanges(true);
  }

  function getCellValue(agentRole: string, actionType: ActionType): AutonomyMode {
    return matrix[agentRole]?.[actionType] || 'notify';
  }

  function getModeColor(mode: AutonomyMode): string {
    return autonomyModes.find((m) => m.value === mode)?.color || 'text-foreground';
  }

  function getSuccessRateColor(rate: number): string {
    if (rate >= 0.95) return 'text-green-600 dark:text-green-400';
    if (rate >= 0.85) return 'text-blue-600 dark:text-blue-400';
    if (rate >= 0.70) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  }

  function getTopRecommendations(): TrustMetric[] {
    return trustMetrics
      .filter((m) => m.recommendation && m.total_attempts >= 5)
      .sort((a, b) => b.success_rate - a.success_rate)
      .slice(0, 5);
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

      {/* Profile Selector */}
      <fieldset className="space-y-2">
        <label htmlFor="autonomy-profile" className="block text-sm font-medium text-foreground">
          Autonomy Profile
        </label>
        <select
          id="autonomy-profile"
          value={selectedProfile}
          onChange={(e) => handleProfileChange(e.target.value as ProfileName)}
          className="w-full max-w-md px-3 py-2 bg-background border border-border rounded-md text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        >
          {profiles.map((profile) => (
            <option key={profile.value} value={profile.value}>
              {profile.label}
            </option>
          ))}
        </select>
        <p className="text-xs text-muted">
          {profiles.find((p) => p.value === selectedProfile)?.description}
        </p>
      </fieldset>

      {/* Progressive Trust Display */}
      {trustMetrics.length > 0 && (
        <div className="space-y-4 p-4 bg-muted/30 border border-border rounded-md">
          <div>
            <h3 className="text-sm font-semibold text-foreground mb-1">Progressive Trust Scores</h3>
            <p className="text-xs text-muted">
              Based on historical agent performance. Higher success rates suggest candidates for increased autonomy.
            </p>
          </div>

          {loadingMetrics ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="animate-spin text-muted" size={20} />
            </div>
          ) : (
            <>
              {/* Trust Metrics Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left py-2 px-2 font-medium text-muted">Agent</th>
                      <th className="text-left py-2 px-2 font-medium text-muted">Action</th>
                      <th className="text-right py-2 px-2 font-medium text-muted">Success Rate</th>
                      <th className="text-right py-2 px-2 font-medium text-muted">Attempts</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trustMetrics.slice(0, 10).map((metric, idx) => (
                      <tr key={idx} className="border-b border-border/50">
                        <td className="py-2 px-2 text-foreground">{metric.agent_role}</td>
                        <td className="py-2 px-2 text-foreground">
                          {actionTypes.find((a) => a.value === metric.action_type)?.label || metric.action_type}
                        </td>
                        <td className={`py-2 px-2 text-right font-medium ${getSuccessRateColor(metric.success_rate)}`}>
                          {(metric.success_rate * 100).toFixed(1)}%
                        </td>
                        <td className="py-2 px-2 text-right text-muted">{metric.total_attempts}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Recommendations */}
              {getTopRecommendations().length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-foreground">Recommendations</h4>
                  <div className="space-y-1">
                    {getTopRecommendations().map((metric, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between px-3 py-2 bg-background border border-border rounded text-xs"
                      >
                        <div className="flex-1">
                          <span className="font-medium text-foreground">{metric.agent_role}</span>
                          <span className="text-muted"> → </span>
                          <span className="text-foreground">
                            {actionTypes.find((a) => a.value === metric.action_type)?.label}
                          </span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className={`font-medium ${getSuccessRateColor(metric.success_rate)}`}>
                            {(metric.success_rate * 100).toFixed(0)}% success
                          </span>
                          <span className="text-muted text-xs">
                            Consider: {autonomyModes.find((m) => m.value === metric.recommendation)?.label}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

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
