'use client';
import { useState } from 'react';
import { Activity, HardDrive, Settings2, ChevronDown, ChevronUp } from 'lucide-react';
import DiagramPanel from './DiagramPanel';
import type { ChatMessage } from '@/hooks/useActiveChat';

interface Props { message: ChatMessage; }

export default function AssistantBubble({ message }: Props) {
  const [detailsOpen, setDetailsOpen] = useState(false);

  return (
    <div className="px-4 py-2">
      <div className="max-w-[90%] space-y-3">
        {/* Narrative */}
        <div className="bg-white/[0.03] border border-white/[0.08] rounded-2xl rounded-tl-sm px-4 py-3">
          <div className="flex items-center gap-2 mb-2">
            <Activity size={12} className="text-cyan-500" />
            <span className="text-[9px] font-mono text-white/40 uppercase tracking-widest">Architect</span>
          </div>
          <p className="text-[12px] font-mono text-white/70 leading-relaxed italic whitespace-pre-wrap">
            {message.content}
          </p>
        </div>

        {/* Diagram */}
        {message.diagram && <DiagramPanel diagram={message.diagram} />}

        {/* Collapsible metadata */}
        {(message.scaling || message.constraints) && (
          <div className="border border-white/5 rounded-lg overflow-hidden">
            <button
              onClick={() => setDetailsOpen(v => !v)}
              className="w-full flex items-center justify-between px-3 py-2 bg-white/[0.02] text-[10px] font-mono text-white/40 uppercase tracking-widest hover:text-white/60 transition-colors"
            >
              <span>Details</span>
              {detailsOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            </button>

            {detailsOpen && (
              <div className="px-3 pb-3 space-y-3 bg-white/[0.01]">
                {message.scaling && (
                  <div className="space-y-1">
                    <div className="flex items-center gap-1.5 pt-2">
                      <HardDrive size={10} className="text-cyan-500" />
                      <span className="text-[9px] font-bold uppercase tracking-widest text-white/40">Reliability & Scale</span>
                    </div>
                    <p className="text-[11px] font-mono text-white/40 bg-white/[0.02] p-2 border border-white/5">
                      {message.scaling}
                    </p>
                  </div>
                )}

                {message.constraints && Object.keys(message.constraints).length > 0 && (
                  <div className="space-y-1">
                    <div className="flex items-center gap-1.5">
                      <Settings2 size={10} className="text-cyan-500" />
                      <span className="text-[9px] font-bold uppercase tracking-widest text-white/40">Context</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {Object.entries(message.constraints).map(([k, v]: [string, any]) => (
                        <div key={k} className="px-2 py-0.5 bg-cyan-500/5 border border-cyan-500/10 text-[9px] font-mono text-cyan-400 uppercase">
                          {k.replace(/_/g, ' ')}: {Array.isArray(v) ? v.join(', ') : String(v)}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
