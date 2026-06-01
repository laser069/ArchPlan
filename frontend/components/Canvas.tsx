'use client';
import React, { useEffect, useRef } from 'react';
import {
  ReactFlow,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
  Handle,
  Position,
  MiniMap,
  Controls,
  Background,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';
import {
  Server, Database, Globe, Shield, Activity,
  Layers, Zap, Cpu, Search, MessageSquare, Monitor
} from 'lucide-react';

const getNodeColor = (type: string): string => {
  const t = (type || '').toLowerCase();
  if (/database|db|postgres|mysql|mongo|dynamo|cassandra|sqlite/.test(t)) return '#10b981';
  if (/cache|redis|memcache/.test(t)) return '#f59e0b';
  if (/queue|kafka|rabbit|sqs|sns|pubsub|bus/.test(t)) return '#f97316';
  if (/auth|jwt|oauth|iam|identity|sso|keycloak/.test(t)) return '#ef4444';
  if (/load.?balancer|lb|haproxy/.test(t)) return '#a78bfa';
  if (/monitor|metric|prometheus|grafana|datadog|log|trace/.test(t)) return '#14b8a6';
  if (/cdn|cloudfront|fastly|akamai/.test(t)) return '#3b82f6';
  if (/search|elastic|solr|algolia/.test(t)) return '#06b6d4';
  if (/gateway|api.?gw|kong|envoy/.test(t)) return '#8b5cf6';
  if (/worker|celery|job|batch|consumer/.test(t)) return '#ec4899';
  if (/proxy|sidecar|istio|linkerd/.test(t)) return '#fb923c';
  if (/network|vpc|subnet|firewall/.test(t)) return '#84cc16';
  if (/storage|s3|blob|gcs|minio|file/.test(t)) return '#22d3ee';
  return '#64748b'; // service / nginx / default
};

const getIcon = (type: string) => {
  const t = (type || '').toLowerCase();
  if (/database|db|postgres|mysql|mongo|dynamo/.test(t)) return <Database size={14} />;
  if (/cache|redis/.test(t)) return <Zap size={14} />;
  if (/queue|kafka|rabbit|bus/.test(t)) return <Layers size={14} />;
  if (/auth|jwt|oauth|iam/.test(t)) return <Shield size={14} />;
  if (/load.?balancer|lb/.test(t)) return <Activity size={14} />;
  if (/monitor|metric|prometheus|log/.test(t)) return <Monitor size={14} />;
  if (/cdn|cloudfront/.test(t)) return <Globe size={14} />;
  if (/search|elastic/.test(t)) return <Search size={14} />;
  if (/gateway|api.?gw|kong/.test(t)) return <Cpu size={14} />;
  if (/worker|celery|job/.test(t)) return <MessageSquare size={14} />;
  return <Server size={14} />;
};

const CustomNode = ({ data }: any) => {
  const color = getNodeColor(data.type);
  const ref = useRef<HTMLDivElement>(null);

  const onEnter = () => {
    if (!ref.current) return;
    ref.current.style.boxShadow = `0 0 0 1px ${color}55, 0 4px 20px ${color}33`;
    ref.current.style.borderColor = `${color}99`;
  };
  const onLeave = () => {
    if (!ref.current) return;
    ref.current.style.boxShadow = '0 2px 8px rgba(0,0,0,0.6)';
    ref.current.style.borderColor = '#1e1e1e';
  };

  return (
    <div
      ref={ref}
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
      style={{
        background: '#0f0f0f',
        border: '1px solid #1e1e1e',
        borderLeft: `4px solid ${color}`,
        borderRadius: '6px',
        minWidth: '180px',
        padding: '10px 12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.6)',
        transition: 'box-shadow 0.2s ease, border-color 0.2s ease',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
        <div style={{ color, marginTop: '1px', flexShrink: 0 }}>
          {getIcon(data.type)}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', minWidth: 0 }}>
          <span
            style={{
              backgroundColor: `${color}22`,
              color,
              border: `1px solid ${color}44`,
              borderRadius: '3px',
              fontSize: '9px',
              fontWeight: 700,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              padding: '1px 5px',
              lineHeight: '1.4',
              display: 'inline-block',
              width: 'fit-content',
            }}
          >
            {data.type_full || data.type}
          </span>
          <span
            style={{
              fontSize: '12px',
              fontWeight: 600,
              color: '#e2e8f0',
              lineHeight: '1.3',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              maxWidth: '140px',
            }}
          >
            {data.label}
          </span>
        </div>
      </div>

      <Handle
        type="target"
        position={Position.Top}
        style={{ background: color, width: '7px', height: '7px', border: '2px solid #0f0f0f', top: '-4px' }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        style={{ background: color, width: '7px', height: '7px', border: '2px solid #0f0f0f', bottom: '-4px' }}
      />
    </div>
  );
};

const getLayoutedElements = (nodes: any[], edges: any[]) => {
  const groupsWithChildren = new Set(nodes.filter(n => n.parentId).map(n => n.parentId));
  const filteredNodes = nodes.filter(node => node.type !== 'group' || groupsWithChildren.has(node.id));

  const g = new dagre.graphlib.Graph({ compound: true });
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

    let x = nodeWithPosition.x - (isGroup ? nodeWithPosition.width / 2 : 90);
    let y = nodeWithPosition.y - (isGroup ? nodeWithPosition.height / 2 : 30);

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
  const [nodes, setNodes, onNodesChange] = useNodesState<any>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<any>([]);
  const { fitView } = useReactFlow();

  useEffect(() => {
    if (initialNodes && initialNodes.length > 0) {
      const layoutedNodes = getLayoutedElements(initialNodes, initialEdges);

      const styledEdges = initialEdges.map(edge => ({
        ...edge,
        type: 'smoothstep',
        animated: true,
        style: { stroke: '#06b6d4', strokeWidth: 1.5, opacity: 0.65 },
      }));

      setNodes(layoutedNodes);
      setEdges(styledEdges);
      setTimeout(() => fitView({ padding: 0.2, duration: 600 }), 50);
    }
  }, [initialNodes, initialEdges, setNodes, setEdges, fitView]);

  return (
    <div className="w-full h-full" style={{ background: '#050505' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        nodeTypes={{ architectureNode: CustomNode }}
        colorMode="dark"
        zoomOnScroll={true}
        maxZoom={2}
        minZoom={0.1}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#1e293b" />
        <Controls />
        <MiniMap
          nodeColor={(node) => getNodeColor(node.data?.type as string)}
          style={{ background: '#0a0a0a', border: '1px solid #1e1e1e' }}
          maskColor="rgba(0,0,0,0.7)"
        />
      </ReactFlow>
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
