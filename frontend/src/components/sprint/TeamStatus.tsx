import { AgentAvatar } from '@/components/shared/AgentAvatar';
import { cn } from '@/lib/utils';
import type { AgentConfig } from '@/lib/types';

type AgentStatus = 'idle' | 'working' | 'waiting' | 'done';

interface TeamStatusProps {
  agents: AgentConfig[];
  agentStatuses?: Record<string, AgentStatus>;
  selectedAgent?: string | null;
  onSelectAgent?: (role: string | null) => void;
}

const statusDot: Record<AgentStatus, string> = {
  idle: 'bg-gray-400',
  working: 'bg-yellow-400 animate-pulse',
  waiting: 'bg-blue-400',
  done: 'bg-green-400',
};

const statusLabel: Record<AgentStatus, string> = {
  idle: 'Idle',
  working: 'Working',
  waiting: 'Waiting',
  done: 'Done',
};

export function TeamStatus({ agents, agentStatuses = {}, selectedAgent, onSelectAgent }: TeamStatusProps) {
  return (
    <div className="space-y-2">
      <h3 className="text-xs font-semibold text-muted uppercase tracking-wider">Team</h3>
      {agents.filter(a => a.enabled).map((agent) => {
        const status: AgentStatus = agentStatuses[agent.agent_role] ?? 'idle';
        const isSelected = selectedAgent === agent.agent_role;

        return (
          <button
            key={agent.agent_role}
            onClick={() => onSelectAgent?.(isSelected ? null : agent.agent_role)}
            className={cn(
              'flex items-center gap-2 w-full px-2 py-1.5 rounded-md text-sm transition-colors',
              isSelected ? 'bg-primary/10' : 'hover:bg-border/50'
            )}
          >
            <AgentAvatar role={agent.agent_role} size="sm" />
            <span className="text-foreground text-xs capitalize flex-1 text-left truncate">
              {agent.agent_role.replace('_', ' ')}
            </span>
            <div className="flex items-center gap-1.5">
              <div className={cn('w-2 h-2 rounded-full', statusDot[status])} />
              <span className="text-muted text-xs">{statusLabel[status]}</span>
            </div>
          </button>
        );
      })}
    </div>
  );
}
