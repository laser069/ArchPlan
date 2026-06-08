'use client';
import { useState } from 'react';
import { Maximize2, X } from 'lucide-react';
import Canvas from './Canvas';
import type { DiagramSnapshot } from '@/hooks/useActiveChat';

interface Props {
  diagram: DiagramSnapshot;
}

export default function DiagramPanel({ diagram }: Props) {
  const [expanded, setExpanded] = useState(false);
  const data = { nodes: diagram.nodes, edges: diagram.edges };

  return (
    <>
      <div className="relative mt-3 rounded-lg overflow-hidden border border-white/10" style={{ height: 380 }}>
        <div className="absolute inset-0 bg-[radial-gradient(#1a1a1a_1px,transparent_1px)] [background-size:32px_32px]">
          <Canvas data={data} />
        </div>
        <button
          onClick={() => setExpanded(true)}
          className="absolute top-2 right-2 z-10 p-1.5 bg-black/60 border border-white/10 rounded text-white/40 hover:text-cyan-400 transition-colors"
        >
          <Maximize2 size={12} />
        </button>
      </div>

      {expanded && (
        <div className="fixed inset-0 z-50 bg-black/90 flex flex-col">
          <div className="flex items-center justify-between px-6 py-3 border-b border-white/10">
            <span className="text-[10px] font-mono text-cyan-500 uppercase tracking-widest">Architecture Diagram</span>
            <button onClick={() => setExpanded(false)} className="text-white/40 hover:text-white transition-colors">
              <X size={18} />
            </button>
          </div>
          <div className="flex-1 bg-[radial-gradient(#1a1a1a_1px,transparent_1px)] [background-size:32px_32px]">
            <Canvas data={data} />
          </div>
        </div>
      )}
    </>
  );
}
