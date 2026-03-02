import { useEffect, useState } from 'react';
import ReactFlow, { Node, Edge, useNodesState, useEdgesState, Controls, Background } from 'reactflow';
import 'reactflow/dist/style.css';
import { api } from '../../api/client';

interface CommNode { id: string; label: string }
interface CommEdge { source: string; target: string; count: number }

interface Props {
  sprintId: string | null;
}

export function CommGraph({ sprintId }: Props) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!sprintId) return;
    setLoading(true);
    api.get<{ nodes: CommNode[]; edges: CommEdge[] }>(`/sprints/${sprintId}/comm-graph`)
      .then(data => {
        const radius = 150;
        const rfNodes: Node[] = data.nodes.map((n, i) => ({
          id: n.id,
          data: { label: n.label },
          position: {
            x: 250 + radius * Math.cos((2 * Math.PI * i) / data.nodes.length),
            y: 200 + radius * Math.sin((2 * Math.PI * i) / data.nodes.length),
          },
          style: { background: '#6366f1', color: 'white', borderRadius: '50%', width: 80, height: 80, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11 },
        }));
        const rfEdges: Edge[] = data.edges.map((e, i) => ({
          id: `e-${i}`,
          source: e.source,
          target: e.target,
          label: `${e.count}`,
          animated: true,
          style: { strokeWidth: Math.min(e.count, 5) },
        }));
        setNodes(rfNodes);
        setEdges(rfEdges);
      })
      .finally(() => setLoading(false));
  }, [sprintId]);

  if (!sprintId) return <p className="text-gray-400 text-sm">Select a sprint to view communication graph.</p>;
  if (loading) return <p className="text-gray-400 text-sm">Loading...</p>;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <h3 className="text-sm font-semibold mb-2">🔗 Communication Graph</h3>
      <div style={{ height: 400 }}>
        <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} fitView>
          <Controls />
          <Background />
        </ReactFlow>
      </div>
    </div>
  );
}
