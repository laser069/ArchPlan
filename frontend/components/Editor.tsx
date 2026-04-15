'use client';
import { useState } from 'react';

export default function Editor({ onGenerate, loading, hasDiagram }: any) {
  const [query, setQuery] = useState('');
  
  return (
    <div className="flex flex-col gap-4">
      <h3 className="text-[10px] uppercase tracking-widest text-black/40 font-bold">Requirements</h3>
      <textarea 
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Describe the system nodes..."
        className="w-full h-48 bg-white border border-black/10 p-4 text-sm focus:border-black outline-none transition-all resize-none font-sans"
      />
      
      <div className="flex flex-col gap-2">
        <button 
          onClick={() => onGenerate(query, false)}
          disabled={loading || !query.trim()}
          className="bg-black text-white text-[10px] font-bold uppercase tracking-widest py-4 hover:bg-zinc-800 disabled:opacity-20 transition-all active:scale-[0.98]"
        >
          {loading ? 'Processing...' : 'Generate New'}
        </button>

        <button 
          onClick={() => onGenerate(query, true)}
          disabled={loading || !hasDiagram || !query.trim()}
          className="border border-black/10 text-black text-[10px] font-bold uppercase tracking-widest py-4 disabled:opacity-5 hover:bg-black hover:text-white transition-all active:scale-[0.98]"
        >
          Refine Design
        </button>
      </div>
    </div>
  );
}