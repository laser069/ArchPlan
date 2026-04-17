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
import { Server, Database, Globe, Shield, Box, Activity } from 'lucide-react';

const CustomNode = ({ data }: any) => {
  const getIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'database': return <Database size={14} />;
      case 'cdn': return <Globe size={14} />;
      case 'auth': return <Shield size={14} />;
      case 'loadbalancer': return <Activity size={14} />;
      case 'server': return <Server size={14} />;
      default: return <Box size={14} />;
    }
  };

  return (
    <div className="px-3 py-2 min-w-[150px] bg-white border border-slate-300 rounded shadow-sm">
      <div className="flex items-center gap-2">
        <div className="text-slate-500">{getIcon(data.type)}</div>
        <div className="flex flex-col">
          <span className="text-[8px] font-bold text-slate-400 uppercase leading-none mb-1">{data.type || 'Service'}</span>
          <span className="text-[11px] text-slate-900 font-semibold truncate max-w-[110px]">{data.label}</span>
        </div>
      </div>
      <Handle type="target" position={Position.Top} className="!bg-slate-400 !w-1 !h-1 !border-none" />
      <Handle type="source" position={Position.Bottom} className="!bg-slate-400 !w-1 !h-1 !border-none" />
    </div>
  );
};

const nodeTypes = {
  architectureNode: CustomNode,
  group: ({ data }: any) => (
    <div className="w-full h-full border border-slate-200 bg-slate-50/40 rounded-lg pointer-events-none">
       <div className="p-2 border-b border-slate-100 bg-white/30">
         <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">{data.label}</span>
       </div>
    </div>
  )
};

const getLayoutedElements = (nodes: any[], edges: any[]) => {
  const groupsWithChildren = new Set(nodes.filter(n => n.parentId).map(n => n.parentId));
  const filteredNodes = nodes.filter(node => node.type !== 'group' || groupsWithChildren.has(node.id));

  const g = new dagre.graphlib.Graph({ compound: true });
  // Increased ranksep to ensure layers have vertical breathing room
  g.setGraph({ rankdir: 'TB', ranksep: 80, nodesep: 50, marginx: 40, marginy: 40 });
  g.setDefaultEdgeLabel(() => ({}));

  filteredNodes.forEach((node) => {
    if (node.type === 'group') {
      g.setNode(node.id, { width: 200, height: 100 });
    } else {
      g.setNode(node.id, { width: 160, height: 50 });
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
    
    // Default Absolute Coordinates
    let x = nodeWithPosition.x - (isGroup ? nodeWithPosition.width / 2 : 80);
    let y = nodeWithPosition.y - (isGroup ? nodeWithPosition.height / 2 : 25);

    // CRITICAL FIX: If node has a parent, calculate its RELATIVE position
    if (node.parentId) {
      const parentPos = g.node(node.parentId);
      x = nodeWithPosition.x - parentPos.x + (parentPos.width / 2) - 80;
      y = nodeWithPosition.y - parentPos.y + (parentPos.height / 2) - 25;
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
    if (initialNodes.length > 0) {
      const layoutedNodes = getLayoutedElements(initialNodes, initialEdges);
      const styledEdges = initialEdges.filter(edge => 
        layoutedNodes.find(n => n.id === edge.source) && layoutedNodes.find(n => n.id === edge.target)
      ).map(edge => ({
        ...edge,
        type: 'smoothstep',
        style: { stroke: '#94a3b8', strokeWidth: 1.5 },
      }));

      setNodes(layoutedNodes);
      setEdges(styledEdges);
      setTimeout(() => fitView({ padding: 0.2, duration: 400 }), 100);
    }
  }, [initialNodes, initialEdges, setNodes, setEdges, fitView]);

  return (
    <div className="w-full h-full bg-[#fcfcfc]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        nodeTypes={nodeTypes}
        colorMode="light"
        zoomOnScroll={false}
        maxZoom={1.5}
        minZoom={0.2}
      />
    </div>
  );
}

export default function Canvas({ data }: { data: any }) {
  if (!data?.nodes) return null;
  return (
    <div className="absolute inset-0">
      <ReactFlowProvider>
        <FlowCanvas initialNodes={data.nodes} initialEdges={data.edges} />
      </ReactFlowProvider>
    </div>
  );
}