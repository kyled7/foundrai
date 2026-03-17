import { Handle, Position, type NodeProps } from 'reactflow';
import { StatusBadge } from '../shared/StatusBadge';

interface GoalNodeData {
  label: string;
  status: string;
}

export function GoalNode({ data }: NodeProps<GoalNodeData>) {
  return (
    <div className="bg-purple-600 text-white rounded-xl px-6 py-3 shadow-lg min-w-[200px]">
      <div className="text-xs uppercase tracking-wide opacity-75">Goal</div>
      <div className="font-semibold mt-1">{data.label}</div>
      {data.status && <StatusBadge status={data.status} className="mt-2 bg-purple-500/30 text-white" />}
      <Handle type="source" position={Position.Bottom} className="!bg-purple-400" />
    </div>
  );
}
