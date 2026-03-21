import { type EdgeProps, getBezierPath, EdgeLabelRenderer, BaseEdge } from 'reactflow';

interface MessageEdgeData {
  messageCount?: number;
  onClick?: (edgeId: string) => void;
}

export function MessageEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  data,
}: EdgeProps<MessageEdgeData>) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const handleClick = () => {
    if (data?.onClick) {
      data.onClick(id);
    }
  };

  return (
    <>
      <BaseEdge path={edgePath} markerEnd={markerEnd} style={style} />
      {data?.messageCount !== undefined && data.messageCount > 0 && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'all',
            }}
            className={`
              bg-blue-500 text-white text-xs font-semibold rounded-full px-2 py-1 shadow-md
              ${data.onClick ? 'cursor-pointer hover:bg-blue-600 transition-colors' : ''}
            `}
            onClick={handleClick}
          >
            {data.messageCount}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}
