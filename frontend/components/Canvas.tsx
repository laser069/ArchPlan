'use client';
import React, { useEffect } from 'react';
import {
  ReactFlow,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
  Handle,
  Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';
import { 
  Server, Database, Globe, Shield, Box, Activity, 
  Layers, Zap, Cpu, Search, MessageSquare, Monitor
} from 'lucide-react';

// Mapper for your Backend Types: S, G, Q, C, R, X, L, D, A, M, E, W, N, P
const getIcon = (type: string) => {
  const t = type?.toUpperCase();
  switch (t) {
    case 'D': return <Database size={14} />; // Database
    case 'X': return <Globe size={14} />;    // CDN
    case 'A': return <Shield size={14} />;   // Auth
    case 'L': return <Activity size={14} />; // Load Balancer
    case 'S': return <Server size={14} />;   // Service
    case 'C': return <Zap size={14} />;      // Cache
    case 'Q': return <Layers size={14} />;   // Queue
    case 'E': return <Search size={14} />;   // Search
    case 'G': return <Cpu size={14} />;      // Gateway
    case 'M': return <Monitor size={14} />;  // Monitor
    case 'W': return <MessageSquare size={14} />; // Worker
    default: return <Box size={14} />;
  }
};

const CustomNode = ({ data }: any) => {
  return (
    <div className="px-3 py-2 min-w-[160px] bg-white border border-slate-200 rounded shadow-sm hover:border-cyan-400 transition-colors">
      <div className="flex items-center gap-2">
        <div className="text-slate-400">{getIcon(data.type)}</div>
        <div className="flex flex-col">
          <span className="text-[7px] font-bold text-cyan-600 uppercase leading-none mb-1 tracking-tighter">
            {data.type_full || data.type}
          </span>
          <span className="text-[11px] text-slate-900 font-semibold truncate max-w-[110px]">
            {data.label}
          </span>
        </div>
      </div>
      <Handle type="target" position={Position.Top} className="!bg-slate-300 !w-1 !h-1 !border-none" />
      <Handle type="source" position={Position.Bottom} className="!bg-slate-300 !w-1 !h-1 !border-none" />
    </div>
  );
};

const getLayoutedElements = (nodes: any[], edges: any[]) => {
  // 1. Identify groups that actually have children
  const groupsWithChildren = new Set(nodes.filter(n => n.parentId).map(n => n.parentId));
  
  // 2. Filter out empty groups (prevents layout crashes)
  const filteredNodes = nodes.filter(node => node.type !== 'group' || groupsWithChildren.has(node.id));

  const g = new dagre.graphlib.Graph({ compound: true });
  
  // TB = Top to Bottom layout. Adjust nodesep/ranksep for spacing.
  g.setGraph({ rankdir: 'TB', ranksep: 100, nodesep: 80, marginx: 50, marginy: 50 });
  g.setDefaultEdgeLabel(() => ({}));

  filteredNodes.forEach((node) => {
    if (node.type === 'group') {
      g.setNode(node.id, { width: 250, height: 150 });
    } else {
      g.setNode(node.id, { width: 180, height: 60 });
    }
    if (node.parentId) g.setParent(node.id, node.parentId);
  });

  edges.forEach((edge) => {
    if (filteredNodes.find(n => n.id === edge.source) && filteredNodes.find(n => n.id === edge.target)) {
      g.setEdge(edge.source, edge.target);
    }
  });

  dagre.layout(g);

  return filteredNodes.map((node) => {
    const nodeWithPosition = g.node(node.id);
    const isGroup = node.type === 'group';
    
    // Calculate centered position
    let x = nodeWithPosition.x - (isGroup ? nodeWithPosition.width / 2 : 90);
    let y = nodeWithPosition.y - (isGroup ? nodeWithPosition.height / 2 : 30);

    // If node is inside a group, Dagre returns absolute coords, 
    // but ReactFlow needs RELATIVE coords for children.
    if (node.parentId) {
      const parentPos = g.node(node.parentId);
      x = nodeWithPosition.x - parentPos.x + (parentPos.width / 2) - 90;
      y = nodeWithPosition.y - parentPos.y + (parentPos.height / 2) - 30;
    }

    return {
      ...node,
      position: { x, y },
      ...(isGroup && {
        style: { width: nodeWithPosition.width, height: nodeWithPosition.height },
      }),
    };
  });
};
function FlowCanvas({ initialNodes, initialEdges }: { initialNodes: any[], initialEdges: any[] }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const { fitView } = useReactFlow();

  useEffect(() => {
    if (initialNodes && initialNodes.length > 0) {
      // 1. Layout nodes using Dagre
      const layoutedNodes = getLayoutedElements(initialNodes, initialEdges);
      
      // 2. Style edges for high visibility
      const styledEdges = initialEdges.map(edge => ({
        ...edge,
        type: 'smoothstep',
        animated: true, // Makes it look "alive"
        style: { stroke: '#06b6d4', strokeWidth: 1, opacity: 0.4 },
      }));

      setNodes(layoutedNodes);
      setEdges(styledEdges);
      
      // 3. Auto-zoom
      setTimeout(() => fitView({ padding: 0.2, duration: 600 }), 50);
    }
  }, [initialNodes, initialEdges, setNodes, setEdges, fitView]);

  return (
    <div className="w-full h-full bg-transparent">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        nodeTypes={{ architectureNode: CustomNode }}
        colorMode="dark" // Matches your black-themed Home.tsx
        zoomOnScroll={true}
        maxZoom={2}
        minZoom={0.1}
      />
    </div>
  );
}

export default function Canvas({ data }: { data: any }) {
  if (!data?.nodes || data.nodes.length === 0) return null;
  return (
    <div className="absolute inset-0">
      <ReactFlowProvider>
        <FlowCanvas initialNodes={data.nodes} initialEdges={data.edges} />
      </ReactFlowProvider>
    </div>
  );
}