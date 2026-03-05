import { useWizard, DEFAULT_AGENTS } from '@/stores/wizard';
import { AgentAvatar } from '@/components/shared/AgentAvatar';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronUp, Plus, Trash2 } from 'lucide-react';
import { useState } from 'react';
import type { AgentFormData } from '@/lib/schemas';

const modelOptions = ['claude-sonnet-4', 'claude-opus-4', 'gpt-4o', 'gpt-4o-mini'];
const autonomyLevels = ['low', 'medium', 'high'] as const;

export function WizardStep2() {
  const { step2Data, setStep2, setStep } = useWizard();
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
  const agents = step2Data.agents;

  const updateAgent = (idx: number, updates: Partial<AgentFormData>) => {
    const updated = agents.map((a, i) => i === idx ? { ...a, ...updates } : a);
    setStep2({ agents: updated });
  };

  const removeAgent = (idx: number) => {
    setStep2({ agents: agents.filter((_, i) => i !== idx) });
  };

  const addAgent = () => {
    setStep2({
      agents: [...agents, { role: 'CustomAgent', model: 'claude-sonnet-4', autonomy: 'medium', enabled: true }],
    });
  };

  const handleNext = () => {
    if (agents.filter(a => a.enabled).length === 0) return;
    setStep(3);
  };

  return (
    <div className="space-y-4">
      {agents.map((agent, idx) => {
        const isExpanded = expandedIdx === idx;
        const isDefault = DEFAULT_AGENTS.some(d => d.role === agent.role);

        return (
          <div key={idx} className="bg-card border border-border rounded-lg overflow-hidden">
            <div
              className="flex items-center gap-3 p-3 cursor-pointer hover:bg-border/30"
              onClick={() => setExpandedIdx(isExpanded ? null : idx)}
            >
              <AgentAvatar role={agent.role.toLowerCase().replace(/([a-z])([A-Z])/g, '$1_$2').toLowerCase()} size="sm" />
              <span className="text-foreground text-sm font-medium flex-1">{agent.role}</span>
              <button
                onClick={(e) => { e.stopPropagation(); updateAgent(idx, { enabled: !agent.enabled }); }}
                className={cn(
                  'px-2 py-0.5 rounded-full text-xs',
                  agent.enabled ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'
                )}
              >
                {agent.enabled ? 'On' : 'Off'}
              </button>
              {!isDefault && (
                <button onClick={(e) => { e.stopPropagation(); removeAgent(idx); }} className="text-muted hover:text-red-400">
                  <Trash2 size={14} />
                </button>
              )}
              {isExpanded ? <ChevronUp size={14} className="text-muted" /> : <ChevronDown size={14} className="text-muted" />}
            </div>

            {isExpanded && (
              <div className="px-3 pb-3 space-y-3 border-t border-border pt-3">
                {!isDefault && (
                  <div>
                    <label className="text-xs text-muted block mb-1">Role Name</label>
                    <input
                      value={agent.role}
                      onChange={(e) => updateAgent(idx, { role: e.target.value })}
                      className="w-full bg-background border border-border rounded-md px-3 py-1.5 text-sm text-foreground"
                    />
                  </div>
                )}
                <div>
                  <label className="text-xs text-muted block mb-1">Model</label>
                  <select
                    value={agent.model}
                    onChange={(e) => updateAgent(idx, { model: e.target.value })}
                    className="w-full bg-background border border-border rounded-md px-3 py-1.5 text-sm text-foreground"
                  >
                    {modelOptions.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-muted block mb-1">Autonomy</label>
                  <div className="flex gap-2">
                    {autonomyLevels.map(l => (
                      <button
                        key={l}
                        type="button"
                        onClick={() => updateAgent(idx, { autonomy: l })}
                        className={cn(
                          'px-3 py-1 rounded-md text-xs capitalize border',
                          agent.autonomy === l ? 'border-primary bg-primary/10 text-primary' : 'border-border text-muted'
                        )}
                      >
                        {l}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="text-xs text-muted block mb-1">Custom Prompt (optional)</label>
                  <textarea
                    value={agent.customPrompt ?? ''}
                    onChange={(e) => updateAgent(idx, { customPrompt: e.target.value || undefined })}
                    rows={2}
                    placeholder="Override the default system prompt..."
                    className="w-full bg-background border border-border rounded-md px-3 py-1.5 text-sm text-foreground placeholder:text-muted resize-none"
                  />
                </div>
              </div>
            )}
          </div>
        );
      })}

      <button
        type="button"
        onClick={addAgent}
        className="flex items-center gap-1.5 px-3 py-2 border border-dashed border-border rounded-lg text-sm text-muted hover:text-foreground hover:border-foreground/30 w-full justify-center"
      >
        <Plus size={14} />
        Add Custom Agent
      </button>

      <div className="flex justify-between pt-2">
        <button onClick={() => setStep(1)} className="px-4 py-2 text-sm text-muted hover:text-foreground">
          ← Back
        </button>
        <button
          onClick={handleNext}
          disabled={agents.filter(a => a.enabled).length === 0}
          className="px-6 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50"
        >
          Next →
        </button>
      </div>
    </div>
  );
}
