'use client';

import { useState, useEffect } from 'react';
import { useArchitecture } from '@/hooks/useArchitecture';
import Editor from '@/components/Editor';
import Canvas from '@/components/Canvas';
import { 
  Cpu, 
  Layers, 
  Terminal, 
  Box, 
  Download, 
  Settings2, 
  RefreshCcw 
} from 'lucide-react';

export default function Home() {
  const { data, loading, generate } = useArchitecture();
  const [provider, setProvider] = useState('groq');
  const [model, setModel] = useState('');

  useEffect(() => {
    const savedProvider = localStorage.getItem('ap_provider');
    const savedModel = localStorage.getItem('ap_model');
    if (savedProvider) setProvider(savedProvider);
    if (savedModel) setModel(savedModel);
  }, []);

  const handleGenerate = (query: string, refine: boolean) => {
    localStorage.setItem('ap_provider', provider);
    localStorage.setItem('ap_model', model);
    generate(query, provider, model, refine);
  };

  return (
    <main className="h-screen flex flex-col overflow-hidden bg-background">
      
      {/* COMMAND HEADER */}
      <nav className="h-14 border-b bg-background flex items-center justify-between px-6 shrink-0 z-20">
        <div className="flex items-center gap-10">
          <div className="flex items-center gap-3">
            <div className="bg-accent p-1.5">
              <Box size={14} className="text-white" />
            </div>
            <h1 className="text-[11px] font-bold tracking-[0.2em] uppercase">
              ArchPlan <span className="font-light opacity-40">Studio</span>
            </h1>
          </div>
          
          <div className="hidden lg:flex items-center gap-6 border-l pl-10 h-14">
            <div className="flex flex-col gap-1">
              <span className="text-[8px] font-bold uppercase opacity-30 tracking-widest">Provider</span>
              <select 
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="text-[10px] font-bold bg-transparent outline-none cursor-pointer hover:text-accent transition-colors uppercase"
              >
                <option value="groq">Groq AI</option>
                <option value="openrouter">OpenRouter</option>
                <option value="gemini">Google Gemini</option>
              </select>
            </div>

            <div className="flex flex-col gap-1 border-l pl-6 h-8 justify-center">
              <span className="text-[8px] font-bold uppercase opacity-30 tracking-widest">Model</span>
              <input 
                type="text" 
                placeholder="ID: Llama-3-70b"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="text-[10px] bg-transparent border-none outline-none w-32 p-0 font-mono focus:text-accent transition-colors"
              />
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {loading && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-accent/5 border border-accent/20">
              <RefreshCcw size={10} className="animate-spin text-accent" />
              <span className="text-[9px] font-bold text-accent uppercase tracking-widest">Synthesizing</span>
            </div>
          )}
          <button className="p-2 hover:bg-muted transition-colors">
            <Settings2 size={16} className="opacity-40" />
          </button>
        </div>
      </nav>

      <div className="flex-1 flex overflow-hidden">
        
        {/* LEFT: SPECS & NODES */}
        <aside className="w-[400px] border-r bg-muted/20 flex flex-col shrink-0">
          <div className="p-6 overflow-y-auto flex-1 custom-scrollbar">
            <div className="flex items-center gap-2 mb-6">
              <Terminal size={12} className="opacity-40" />
              <h2 className="text-[10px] font-bold uppercase tracking-widest">Specifications</h2>
            </div>
            
            <Editor onGenerate={handleGenerate} loading={loading} hasDiagram={!!data?.diagram} />
            
            {data?.components && data.components.length > 0 && (
              <div className="mt-12">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Layers size={12} className="opacity-40" />
                    <h2 className="text-[10px] font-bold uppercase tracking-widest">Inventory</h2>
                  </div>
                </div>
                
                <div className="border bg-background divide-y">
                  {data.components.map((c: any, i: number) => (
                    <div key={i} className="p-3 flex justify-between items-center group border-l-2 border-transparent hover:border-accent hover:bg-accent/5 transition-all">
                      <div className="flex items-center gap-3">
                        <Cpu size={12} className="opacity-20 group-hover:text-accent transition-all" />
                        <span className="text-[11px] font-bold uppercase tracking-tight">{c.name}</span>
                      </div>
                      <span className="text-[9px] opacity-30 uppercase italic">{c.type}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </aside>

        {/* CENTER: DRAFTING CANVAS */}
        <section className="flex-1 relative bg-blueprint flex flex-col">
          <div className="h-10 border-b bg-background/60 backdrop-blur-md flex items-center px-6 justify-between shrink-0 z-10">
            <span className="text-[9px] font-bold opacity-30 uppercase tracking-widest">Viewport // 1.0</span>
            {data?.diagram && (
              <button 
                onClick={() => navigator.clipboard.writeText(data.diagram)}
                className="text-[9px] font-bold text-accent hover:underline uppercase"
              >
                Copy Source
              </button>
            )}
          </div>

          <div className="flex-1 overflow-auto flex items-center justify-center p-12">
            <Canvas diagram={data?.diagram} />
          </div>
        </section>

        {/* RIGHT: ANALYSIS */}
        <aside className="w-[320px] border-l bg-muted/20 flex flex-col shrink-0">
          <div className="p-8 overflow-y-auto flex-1 space-y-12 custom-scrollbar">
            <section>
              <h2 className="text-[10px] font-bold uppercase tracking-widest mb-4 opacity-40">Rationale</h2>
              <div className="text-[12px] leading-relaxed text-foreground/80 font-serif italic border-l-2 border-accent pl-6 py-2">
                {data?.architecture || "Awaiting sequence..."}
              </div>
            </section>

            <section>
              <h2 className="text-[10px] font-bold uppercase tracking-widest mb-4 opacity-40">Risk Assessment</h2>
              <div className="text-[11px] leading-relaxed text-foreground/60 bg-background p-4 border border-dashed">
                {data?.scaling || "No data available."}
              </div>
            </section>
          </div>
          
          <div className="p-6 border-t bg-background">
            <button className="w-full bg-foreground text-background py-3.5 text-[10px] font-bold uppercase tracking-widest hover:bg-accent hover:text-white transition-all">
              Export Blueprint
            </button>
          </div>
        </aside>
      </div>

      {/* FOOTER */}
      <footer className="h-7 border-t bg-background px-4 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-1 h-1 ${loading ? 'bg-accent animate-pulse' : 'bg-emerald-500'}`} />
            <span className="text-[8px] font-bold uppercase tracking-widest opacity-40">{loading ? 'Computing' : 'Synchronized'}</span>
          </div>
        </div>
        <div className="text-[8px] font-bold uppercase tracking-widest opacity-20">
          Precision Studio v3.0
        </div>
      </footer>
    </main>
  );
}