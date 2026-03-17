import { Handle, Position, type NodeProps } from 'reactflow';
import { AgentAvatar } from '../shared/AgentAvatar';
import { StatusBadge } from '../shared/StatusBadge';
import { cn } from '../../utils/cn';
import type { AgentRole, TaskStatus } from '../../types';

interface TaskNodeData {
  label: string;
  status: TaskStatus;
  assigned_to: AgentRole;
}

const STATUS_COLORS: Record<string, string> = {
  backlog: 'border-gray-300 bg-gray-50',
  in_progress: 'border-blue-400 bg-blue-50',
  in_review: 'border-yellow-400 bg-yellow-50',
  done: 'border-green-400 bg-green-50',
  failed: 'border-red-400 bg-red-50',
  blocked: 'border-gray-400 bg-gray-100',
};

export function TaskNode({ data }: NodeProps<TaskNodeData>) {
  return (
    <div className={cn(
      'border-2 rounded-lg px-4 py-2 shadow-sm min-w-[180px]',
      STATUS_COLORS[data.status] ?? 'border-gray-300 bg-gray-50'
    )}>
      <Handle type="target" position={Position.Top} />
      <div className="flex items-center gap-2">
        <AgentAvatar role={data.assigned_to} size="xs" />
        <span className="text-sm font-medium">{data.label}</span>
      </div>
      <StatusBadge status={data.status} size="sm" className="mt-1" />
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
