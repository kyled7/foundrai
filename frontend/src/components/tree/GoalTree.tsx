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

function TreeSkeleton() {
  return (
    <div className="h-full w-full flex items-center justify-center bg-white dark:bg-gray-900">
      <div className="text-center space-y-4">
        <div className="flex justify-center gap-4">
          <div className="w-32 h-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
          <div className="w-32 h-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
        </div>
        <div className="flex justify-center gap-4">
          <div className="w-32 h-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
          <div className="w-32 h-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
          <div className="w-32 h-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-4">Loading goal tree...</p>
      </div>
    </div>
  );
}

export function GoalTree({ sprintId }: Props) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [isEmpty, setIsEmpty] = useState(false);

  const loadTree = useCallback(async () => {
    setLoading(true);
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
      const taskNodes = rfNodes.filter(n => n.type === 'task');
      if (taskNodes.length === 0) {
        setIsEmpty(true);
      } else {
        setIsEmpty(false);
        const laid = layoutTree(rfNodes, rfEdges);
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
    loadTree();
  }, [loadTree]);

  const memoNodeTypes = useMemo(() => nodeTypes, []);

  if (loading) {
    return <TreeSkeleton />;
  }

  if (isEmpty) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-white dark:bg-gray-900">
        <div className="text-center">
          <p className="text-4xl mb-2">🌳</p>
          <p className="text-lg font-medium text-gray-600 dark:text-gray-400">No task decomposition yet</p>
          <p className="text-sm text-gray-500 dark:text-gray-500">Tasks will appear here once planning is complete.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full bg-white dark:bg-gray-900">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={memoNodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background className="dark:bg-gray-900" />
        <Controls />
        <MiniMap className="dark:bg-gray-800" />
      </ReactFlow>
    </div>
  );
}
