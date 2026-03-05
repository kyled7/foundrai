import { AgentAvatar } from '@/components/shared/AgentAvatar';
import type { WSEvent } from '@/lib/types';
import { CheckCircle, AlertTriangle, FileText, Brain, MessageSquare, DollarSign } from 'lucide-react';

interface FeedEventProps {
  event: WSEvent;
  onApprove?: (approvalId: string) => void;
  onReject?: (approvalId: string) => void;
}

export function FeedEvent({ event, onApprove, onReject }: FeedEventProps) {
  const time = new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const data = event.data;
  const agentRole = (data.agent_id ?? data.agent_role ?? '') as string;

  // Determine event styling
  switch (event.type) {
    case 'agent.thinking':
      return (
        <div className="flex gap-3 py-2 opacity-70">
          <Brain size={14} className="text-muted mt-0.5 shrink-0" />
          <div className="min-w-0">
            <p className="text-xs text-muted italic">(data.content as string) ?? "Thinking..."</p>
            <span className="text-[10px] text-muted">{time}</span>
          </div>
        </div>
      );

    case 'agent.message':
      return (
        <div className="flex gap-3 py-2">
          <AgentAvatar role={agentRole} size="sm" />
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-0.5">
              <span className="text-xs font-medium text-foreground capitalize">{agentRole.replace('_', ' ')}</span>
              <span className="text-[10px] text-muted">{time}</span>
            </div>
            <div className="bg-background rounded-lg px-3 py-2">
              <p className="text-sm text-foreground whitespace-pre-wrap">{String(data.content)}</p>
            </div>
          </div>
        </div>
      );

    case 'agent.action':
      return (
        <div className="flex gap-3 py-2">
          <FileText size={14} className="text-blue-400 mt-0.5 shrink-0" />
          <div className="min-w-0">
            <p className="text-xs text-foreground">{String(data.description ?? data.action)}</p>
            {data.file_path ? (
              <code className="text-[10px] text-primary font-mono">{String(data.file_path)}</code>
            ) : null}
            <span className="text-[10px] text-muted ml-2">{time}</span>
          </div>
        </div>
      );

    case 'task.completed':
      return (
        <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3 my-1">
          <div className="flex items-center gap-2">
            <CheckCircle size={14} className="text-green-400" />
            <span className="text-sm text-green-400 font-medium">Task completed</span>
            <span className="text-[10px] text-muted ml-auto">{time}</span>
          </div>
          <p className="text-xs text-foreground mt-1">{String(data.title ?? data.task_id)}</p>
        </div>
      );

    case 'task.failed':
      return (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 my-1">
          <div className="flex items-center gap-2">
            <AlertTriangle size={14} className="text-red-400" />
            <span className="text-sm text-red-400 font-medium">Task failed</span>
            <span className="text-[10px] text-muted ml-auto">{time}</span>
          </div>
          <p className="text-xs text-foreground mt-1">{String(data.title ?? data.error)}</p>
        </div>
      );

    case 'approval.requested':
      return (
        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3 my-1">
          <div className="flex items-center gap-2">
            <AlertTriangle size={14} className="text-yellow-400" />
            <span className="text-sm text-yellow-400 font-medium">Approval Needed</span>
            <span className="text-[10px] text-muted ml-auto">{time}</span>
          </div>
          <p className="text-xs text-foreground mt-1">{String(data.title)}</p>
          <p className="text-xs text-muted">{String(data.description)}</p>
          {onApprove && onReject && (
            <div className="flex gap-2 mt-2">
              <button
                onClick={() => onApprove(data.approval_id as string)}
                className="px-3 py-1 bg-green-500/20 text-green-400 rounded text-xs font-medium hover:bg-green-500/30"
              >
                ✅ Approve (A)
              </button>
              <button
                onClick={() => onReject(data.approval_id as string)}
                className="px-3 py-1 bg-red-500/20 text-red-400 rounded text-xs font-medium hover:bg-red-500/30"
              >
                ❌ Reject (R)
              </button>
            </div>
          )}
        </div>
      );

    case 'budget.warning':
      return (
        <div className="flex gap-3 py-2">
          <DollarSign size={14} className="text-yellow-400 mt-0.5 shrink-0" />
          <p className="text-xs text-yellow-400">{String(data.message ?? "Budget warning")}</p>
        </div>
      );

    case 'sprint.completed':
      return (
        <div className="bg-primary/10 border border-primary/20 rounded-lg p-4 my-2 text-center">
          <p className="text-lg">🎉</p>
          <p className="text-sm font-medium text-primary mt-1">Sprint Completed!</p>
          <p className="text-xs text-muted mt-1">{time}</p>
        </div>
      );

    default:
      return (
        <div className="flex gap-3 py-1">
          <MessageSquare size={12} className="text-muted mt-0.5 shrink-0" />
          <p className="text-xs text-muted">{event.type}: {JSON.stringify(data).slice(0, 100)}</p>
        </div>
      );
  }
}
