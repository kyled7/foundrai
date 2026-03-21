import { Handle, Position, type NodeProps } from 'reactflow';

interface AgentNodeData {
  label: string;
  role: string;
  messageCount?: number;
}

export function AgentNode({ data }: NodeProps<AgentNodeData>) {
  return (
    <div className="bg-blue-600 text-white rounded-xl px-6 py-3 shadow-lg min-w-[200px]">
      <Handle type="target" position={Position.Top} className="!bg-blue-400" />
      <div className="text-xs uppercase tracking-wide opacity-75">Agent</div>
      <div className="font-semibold mt-1">{data.label}</div>
      {data.role && (
        <div className="text-xs mt-1 opacity-90 capitalize">
          {data.role.replace('_', ' ')}
        </div>
      )}
      {data.messageCount !== undefined && data.messageCount > 0 && (
        <div className="text-xs mt-2 bg-blue-500/30 rounded px-2 py-1 inline-block">
          {data.messageCount} {data.messageCount === 1 ? 'message' : 'messages'}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} className="!bg-blue-400" />
    </div>
  );
}
