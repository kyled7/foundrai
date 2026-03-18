import { useEffect, useState } from 'react';
import type { AgentConfig } from '../../types';
import { AgentAvatar } from '../shared/AgentAvatar';

interface TeamPanelProps {
  projectId: string;
}

const AUTONOMY_LEVELS = [
  { value: 'auto_approve', label: 'Auto Approve' },
  { value: 'notify', label: 'Notify' },
  { value: 'require_approval', label: 'Require Approval' },
  { value: 'block', label: 'Block' },
];

const MODELS = [
  'anthropic/claude-sonnet-4-20250514',
  'openai/gpt-4o',
  'openai/gpt-4o-mini',
  'anthropic/claude-haiku-4-20250414',
];

export function TeamPanel({ projectId }: TeamPanelProps) {
  const [agents, setAgents] = useState<AgentConfig[]>([]);
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/projects/${projectId}/agents`)
      .then((r) => r.json())
      .then((data) => setAgents(data.agents || []))
      .catch(() => {});
  }, [projectId]);

  const updateAgent = async (role: string, update: Partial<AgentConfig>) => {
    setSaving(role);
    try {
      const res = await fetch(`/api/projects/${projectId}/agents/${role}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(update),
      });
      if (res.ok) {
        const updated = await res.json();
        setAgents((prev) =>
          prev.map((a) => (a.agent_role === role ? { ...a, ...updated } : a))
        );
      }
    } finally {
      setSaving(null);
    }
  };

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-semibold">Team Configuration</h2>
      <p className="text-sm text-gray-500">
        Configure autonomy levels and models for each agent role.
      </p>
      <div className="space-y-3">
        {agents.map((agent) => (
          <div
            key={agent.agent_role}
            className="flex items-center gap-4 p-4 bg-white dark:bg-gray-800 rounded-lg border"
          >
            <AgentAvatar role={agent.agent_role} size="md" />
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="font-medium capitalize">
                  {agent.agent_role.replace('_', ' ')}
                </span>
                <label className="flex items-center gap-1 text-xs">
                  <input
                    type="checkbox"
                    checked={agent.enabled}
                    onChange={(e) =>
                      updateAgent(agent.agent_role, { enabled: e.target.checked })
                    }
                  />
                  Enabled
                </label>
              </div>
              <div className="flex gap-3 mt-2">
                <select
                  value={agent.autonomy_level}
                  onChange={(e) =>
                    updateAgent(agent.agent_role, { autonomy_level: e.target.value })
                  }
                  disabled={saving === agent.agent_role}
                  className="text-sm border rounded px-2 py-1"
                >
                  {AUTONOMY_LEVELS.map((l) => (
                    <option key={l.value} value={l.value}>
                      {l.label}
                    </option>
                  ))}
                </select>
                <select
                  value={agent.model}
                  onChange={(e) =>
                    updateAgent(agent.agent_role, { model: e.target.value })
                  }
                  disabled={saving === agent.agent_role}
                  className="text-sm border rounded px-2 py-1"
                >
                  {MODELS.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
