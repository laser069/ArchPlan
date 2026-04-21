'use client';

import { useState } from 'react';
import { Send, Sparkles, Command } from 'lucide-react';

export default function Editor({ onGenerate, loading, hasDiagram }: any) {
  const [query, setQuery] = useState('');
  
  const handleAction = (isRefine: boolean) => {
    if (!query.trim()) return;
    onGenerate(query, isRefine);
    // Optional: Clear query after generation to encourage fresh refinement instructions
    // setQuery(''); 
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="relative group">
        <div className="absolute -top-3 left-3 px-2 bg-[#0A0A0A] text-[9px] text-white/30 font-mono flex items-center gap-1 border border-white/5">
          <Command size={8} /> 
          {hasDiagram ? "REFINEMENT_MODE" : "INITIAL_GEN_MODE"}
        </div>
        
        <textarea 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={hasDiagram ? "E.g., 'Add a Redis cache between the API and DB'..." : "E.g., 'A high-traffic e-commerce system with microservices'..."}
          className="w-full h-80 bg-black/40 border border-white/10 p-5 text-[12px] font-mono leading-relaxed outline-none focus:border-cyan-500/50 transition-all resize-none placeholder:text-white/10 rounded-lg"
        />
        
        <div className="absolute bottom-3 right-3 text-[9px] font-mono text-white/10 tabular-nums">
          LEN: {query.length}
        </div>
      </div>
      
      <div className="grid grid-cols-5 gap-2">
        <button 
          onClick={() => handleAction(false)}
          disabled={loading || !query.trim()}
          className="col-span-3 flex items-center justify-center gap-3 bg-cyan-600 hover:bg-cyan-500 text-black py-4 text-[10px] font-black uppercase tracking-[0.2em] disabled:opacity-20 transition-all rounded-lg"
        >
          {loading ? (
            <div className="h-3 w-3 border-2 border-black/30 border-t-black animate-spin rounded-full" />
          ) : (
            <Send size={12} />
          )}
          <span>Generate New</span>
        </button>

        <button 
          onClick={() => handleAction(true)}
          disabled={loading || !hasDiagram || !query.trim()}
          className="col-span-2 flex items-center justify-center gap-3 border border-white/10 text-white/40 py-4 text-[10px] font-bold uppercase tracking-widest hover:bg-white/5 hover:text-cyan-400 disabled:opacity-5 transition-all rounded-lg group"
        >
          <Sparkles size={12} className="group-hover:animate-pulse" />
          <span>Refine</span>
        </button>
      </div>
      
      {hasDiagram && (
        <p className="text-[10px] text-white/20 font-mono italic text-center">
          Refining uses previous constraints to maintain consistency.
        </p>
      )}
    </div>
  );
}