'use client';

import { useState } from 'react';
import { Send, Sparkles } from 'lucide-react';

export default function Editor({ onGenerate, loading, hasDiagram }: any) {
  const [query, setQuery] = useState('');
  
  return (
    <div className="flex flex-col gap-4">
      <div className="relative">
        <textarea 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="DESCRIBE SYSTEM ARCHITECTURE..."
          className="w-full h-80 bg-background border border-border p-5 text-[12px] font-mono leading-relaxed outline-none focus:ring-1 focus:ring-accent focus:border-accent transition-all resize-none placeholder:opacity-20"
        />
        <div className="absolute bottom-3 right-3 text-[9px] font-mono opacity-20 pointer-events-none">
          {query.length}
        </div>
      </div>
      
      <div className="flex flex-col gap-2">
        <button 
          onClick={() => onGenerate(query, false)}
          disabled={loading || !query.trim()}
          className="flex items-center justify-center gap-3 bg-accent text-white py-4 text-[10px] font-bold uppercase tracking-widest hover:brightness-110 disabled:opacity-20 transition-all"
        >
          {loading ? (
            <div className="h-3 w-3 border-2 border-white/30 border-t-white animate-spin" />
          ) : (
            <Send size={12} />
          )}
          <span>Generate System</span>
        </button>

        <button 
          onClick={() => onGenerate(query, true)}
          disabled={loading || !hasDiagram || !query.trim()}
          className="flex items-center justify-center gap-3 border border-accent text-accent py-4 text-[10px] font-bold uppercase tracking-widest hover:bg-accent hover:text-white disabled:opacity-5 transition-all"
        >
          <Sparkles size={12} />
          <span>Refine Nodes</span>
        </button>
      </div>
    </div>
  );
}