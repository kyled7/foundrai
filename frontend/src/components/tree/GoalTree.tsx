import { useEffect, useMemo, useCallback } from 'react';
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
import { GoalNode } from './GoalNode';
import { TaskNode } from './TaskNode';
import { getGoalTree } from '../../api/sprints';
import type { GoalTreeResponse } from '../../types';

const nodeTypes = { goal: GoalNode, task: TaskNode };

function layoutTree(nodes: Node[], edges: Edge[]): { nodes: Node[]; edges: Edge[] } {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'TB', nodesep: 60, ranksep: 80 });

  nodes.forEach((node) => {
    g.setNode(node.id, { width: 200, height: 80 });
  });
  edges.forEach((edge) => {
    g.setEdge(edge.source, edge.target);
  });

  dagre.layout(g);

  const layoutedNodes = nodes.map((node) => {
    const pos = g.node(node.id);
    return { ...node, position: { x: pos.x - 100, y: pos.y - 40 } };
  });

  return { nodes: layoutedNodes, edges };
}

interface Props {
  sprintId: string;
}

export function GoalTree({ sprintId }: Props) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const loadTree = useCallback(async () => {
    try {
      const data: GoalTreeResponse = await getGoalTree(sprintId);
      const rfNodes: Node[] = data.nodes.map((n) => ({
        id: n.id,
        type: n.type,
        data: { label: n.label, status: n.status, assigned_to: n.assigned_to },
        position: { x: 0, y: 0 },
      }));
      const rfEdges: Edge[] = data.edges.map((e) => ({
        id: `${e.source}-${e.target}`,
        source: e.source,
        target: e.target,
        type: 'smoothstep',
        animated: e.type === 'decomposition',
        style: e.type === 'dependency'
          ? { strokeDasharray: '5 5', stroke: '#3b82f6' }
          : { stroke: '#9ca3af' },
      }));
      const laid = layoutTree(rfNodes, rfEdges);
      setNodes(laid.nodes);
      setEdges(laid.edges);
    } catch {
      // Sprint may not have tasks yet
    }
  }, [sprintId, setNodes, setEdges]);

  useEffect(() => {
    loadTree();
  }, [loadTree]);

  const memoNodeTypes = useMemo(() => nodeTypes, []);

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={memoNodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}
