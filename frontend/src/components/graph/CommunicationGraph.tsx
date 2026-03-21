import { useEffect, useMemo, useCallback, useState } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
} from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from '@dagrejs/dagre';
import { AgentNode } from './AgentNode';
import { getCommunicationGraph } from '../../api/sprints';
import type { CommunicationGraphResponse } from '../../types';

const nodeTypes = { agent: AgentNode };

function layoutGraph(nodes: Node[], edges: Edge[]): { nodes: Node[]; edges: Edge[] } {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'LR', nodesep: 80, ranksep: 120 });

  nodes.forEach((node) => {
    g.setNode(node.id, { width: 220, height: 100 });
  });
  edges.forEach((edge) => {
    g.setEdge(edge.source, edge.target);
  });

  dagre.layout(g);

  const layoutedNodes = nodes.map((node) => {
    const pos = g.node(node.id);
    return { ...node, position: { x: pos.x - 110, y: pos.y - 50 } };
  });

  return { nodes: layoutedNodes, edges };
}

interface Props {
  sprintId: string;
}

function GraphSkeleton() {
  return (
    <div className="h-full w-full flex items-center justify-center bg-white dark:bg-gray-900">
      <div className="text-center space-y-4">
        <div className="flex justify-center gap-4">
          <div className="w-48 h-20 bg-gray-200 dark:bg-gray-700 rounded-xl animate-pulse" />
          <div className="w-48 h-20 bg-gray-200 dark:bg-gray-700 rounded-xl animate-pulse" />
        </div>
        <div className="flex justify-center gap-4">
          <div className="w-48 h-20 bg-gray-200 dark:bg-gray-700 rounded-xl animate-pulse" />
          <div className="w-48 h-20 bg-gray-200 dark:bg-gray-700 rounded-xl animate-pulse" />
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-4">Loading communication graph...</p>
      </div>
    </div>
  );
}

export function CommunicationGraph({ sprintId }: Props) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [isEmpty, setIsEmpty] = useState(false);
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);

  const loadGraph = useCallback(async () => {
    setLoading(true);
    try {
      const data: CommunicationGraphResponse = await getCommunicationGraph(sprintId);

      if (data.nodes.length === 0) {
        setIsEmpty(true);
      } else {
        setIsEmpty(false);

        const rfNodes: Node[] = data.nodes.map((n) => ({
          id: n.id,
          type: 'agent',
          data: {
            label: n.label,
            role: n.id,
          },
          position: { x: 0, y: 0 },
        }));

        const rfEdges: Edge[] = data.edges.map((e) => ({
          id: `${e.source}-${e.target}`,
          source: e.source,
          target: e.target,
          type: 'smoothstep',
          animated: true,
          label: `${e.count}`,
          labelStyle: {
            fontSize: 12,
            fontWeight: 600,
            fill: '#6b7280',
          },
          labelBgStyle: {
            fill: '#ffffff',
            fillOpacity: 0.9,
          },
          labelBgPadding: [4, 4],
          labelBgBorderRadius: 4,
          style: {
            stroke: '#3b82f6',
            strokeWidth: Math.min(1 + e.count * 0.5, 5),
          },
          data: { count: e.count },
        }));

        const laid = layoutGraph(rfNodes, rfEdges);
        setNodes(laid.nodes);
        setEdges(laid.edges);
      }
    } catch {
      setIsEmpty(true);
    } finally {
      setLoading(false);
    }
  }, [sprintId, setNodes, setEdges]);

  useEffect(() => {
    loadGraph();
  }, [loadGraph]);

  const memoNodeTypes = useMemo(() => nodeTypes, []);

  const onEdgeClick = useCallback((_event: React.MouseEvent, edge: Edge) => {
    setSelectedEdge(edge);
  }, []);

  if (loading) {
    return <GraphSkeleton />;
  }

  if (isEmpty) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-white dark:bg-gray-900">
        <div className="text-center">
          <p className="text-4xl mb-2">💬</p>
          <p className="text-lg font-medium text-gray-600 dark:text-gray-400">No agent communication yet</p>
          <p className="text-sm text-gray-500 dark:text-gray-500">Messages will appear here once agents start communicating.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full bg-white dark:bg-gray-900 relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={memoNodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onEdgeClick={onEdgeClick}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background className="dark:bg-gray-900" />
        <Controls />
        <MiniMap className="dark:bg-gray-800" />
      </ReactFlow>

      {selectedEdge && (
        <div className="absolute top-4 right-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 max-w-md border border-gray-200 dark:border-gray-700">
          <div className="flex items-start justify-between mb-2">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">Message Details</h3>
            <button
              onClick={() => setSelectedEdge(null)}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              ✕
            </button>
          </div>
          <div className="space-y-2 text-sm">
            <div>
              <span className="font-medium text-gray-700 dark:text-gray-300">From:</span>{' '}
              <span className="text-gray-900 dark:text-gray-100 capitalize">
                {selectedEdge.source.replace('_', ' ')}
              </span>
            </div>
            <div>
              <span className="font-medium text-gray-700 dark:text-gray-300">To:</span>{' '}
              <span className="text-gray-900 dark:text-gray-100 capitalize">
                {selectedEdge.target.replace('_', ' ')}
              </span>
            </div>
            <div>
              <span className="font-medium text-gray-700 dark:text-gray-300">Message Count:</span>{' '}
              <span className="text-gray-900 dark:text-gray-100">
                {(selectedEdge.data as { count: number }).count}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
