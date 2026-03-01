import { useState } from 'react';
import type { WSMessage } from '../../types';
import { AgentAvatar } from '../shared/AgentAvatar';
import { TimeAgo } from '../shared/TimeAgo';

const EVENT_CONFIG: Record<string, { icon: string; label: string }> = {
  'agent.message':        { icon: '💬', label: 'Message' },
  'agent.thinking':       { icon: '🧠', label: 'Thinking' },
  'agent.tool_call':      { icon: '🔧', label: 'Tool Call' },
  'agent.tool_result':    { icon: '✅', label: 'Tool Result' },
  'task.status_changed':  { icon: '📋', label: 'Task Update' },
  'task.created':         { icon: '➕', label: 'New Task' },
  'sprint.status_changed':{ icon: '🏃', label: 'Sprint Update' },
  'sprint.started':       { icon: '🚀', label: 'Sprint Started' },
  'sprint.planning_started': { icon: '📋', label: 'Planning Started' },
  'sprint.planning_completed': { icon: '✅', label: 'Planning Done' },
  'sprint.review_completed': { icon: '🔍', label: 'Review Done' },
  'sprint.retrospective_started': { icon: '🔄', label: 'Retrospective' },
  'sprint.retrospective_completed': { icon: '🎯', label: 'Retro Done' },
  'approval.requested':   { icon: '⚠️', label: 'Approval Needed' },
  'artifact.created':     { icon: '📄', label: 'Artifact' },
};

function renderContent(event: WSMessage): string {
  const d = event.data as Record<string, unknown>;
  switch (event.type) {
    case 'agent.message':
      return String(d.content ?? d.message ?? '');
    case 'task.status_changed':
      return `${d.task_title || d.title || 'Task'} → ${d.status}`;
    case 'task.created':
      return `New task: ${(d.task as Record<string, unknown>)?.title ?? ''}`;
    case 'sprint.status_changed':
      return `Sprint → ${d.status}`;
    case 'sprint.started':
      return `Sprint started: ${d.goal ?? ''}`;
    case 'sprint.planning_started':
      return `Planning sprint: ${d.goal ?? ''}`;
    case 'sprint.planning_completed':
      return `Planning complete — ${d.task_count ?? 0} tasks created`;
    case 'sprint.review_completed':
      return `Review: ${d.completed_count ?? 0} passed, ${d.failed_count ?? 0} failed`;
    case 'sprint.retrospective_started':
      return 'Running retrospective...';
    case 'sprint.retrospective_completed':
      return `Retro: ${d.learnings_count ?? 0} learnings captured`;
    case 'agent.thinking':
      return String(d.content ?? '').slice(0, 200);
    case 'agent.tool_call':
      return `Called ${d.tool_name}`;
    default:
      return JSON.stringify(d).slice(0, 150);
  }
}

interface Props {
  event: WSMessage;
}

export function FeedEntry({ event }: Props) {
  const [expanded, setExpanded] = useState(false);
  const config = EVENT_CONFIG[event.type] ?? { icon: '📌', label: event.type };
  const agentId = String((event.data as Record<string, unknown>).agent_id ?? (event.data as Record<string, unknown>).from_agent ?? 'system');

  return (
    <div className="flex gap-3 text-sm">
      <div className="flex flex-col items-center">
        <AgentAvatar role={agentId} size="xs" />
        <div className="w-px flex-1 bg-gray-200 dark:bg-gray-700" />
      </div>

      <div className="flex-1 pb-4">
        <div className="flex items-center gap-2">
          <span>{config.icon}</span>
          <span className="font-medium capitalize">{agentId.replace('_', ' ')}</span>
          <span className="text-gray-400">·</span>
          <TimeAgo timestamp={event.timestamp} />
        </div>

        <div className="mt-1 text-gray-700 dark:text-gray-300">
          {renderContent(event)}
        </div>

        {(event.type === 'agent.thinking' || event.type === 'agent.tool_call') && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-blue-500 mt-1 hover:underline"
          >
            {expanded ? 'Collapse' : 'Show details'}
          </button>
        )}
        {expanded && (
          <pre className="mt-2 bg-gray-50 dark:bg-gray-900 rounded p-2 text-xs overflow-x-auto whitespace-pre-wrap">
            {JSON.stringify(event.data, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
