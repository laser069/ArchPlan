'use client';

import { useState, useEffect } from 'react';
import { useArchitecture } from '@/hooks/useArchitecture';
import Editor from '@/components/Editor';
import Canvas from '@/components/Canvas';

export default function Home() {
  const { data, loading, generate, setData } = useArchitecture();
  const [provider, setProvider] = useState('groq');
  const [model, setModel] = useState('');

  // Persist settings
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

  const resetWorkspace = () => {
    if (confirm("Reset all data?")) {
      localStorage.clear();
      window.location.reload();
    }
  };

  return (
    <main className="h-screen flex flex-col bg-white text-black font-sans selection:bg-black selection:text-white">
      {/* Navigation with Settings */}
      <nav className="h-16 border-b border-black/5 flex items-center justify-between px-8">
        <div className="flex items-center gap-10">
          <span className="text-xs font-black uppercase tracking-widest">ArchPlan</span>
          
          <div className="flex items-center gap-6 border-l border-black/10 pl-10">
            <select 
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="text-[10px] uppercase font-bold tracking-tight bg-transparent outline-none cursor-pointer hover:opacity-50"
            >
              <option value="groq">Groq</option>
              <option value="openrouter">OpenRouter</option>
              <option value="gemini">Gemini</option>
              <option value="ollama">Ollama</option>
            </select>

            <input 
              type="text" 
              placeholder="MODEL ID"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="text-[10px] border-b border-black/10 focus:border-black outline-none w-32 pb-1 transition-all"
            />
          </div>
        </div>

        {loading && (
          <div className="flex items-center gap-2 animate-in fade-in">
            <div className="h-1 w-1 bg-black animate-ping" />
            <span className="text-[9px] uppercase tracking-widest opacity-50">Processing</span>
          </div>
        )}
      </nav>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: Controls & Components */}
        <aside className="w-[350px] border-r border-black/5 p-8 flex flex-col gap-10 overflow-y-auto">
          <Editor onGenerate={handleGenerate} loading={loading} hasDiagram={!!data?.diagram} />
          
          {data?.components && data.components.length > 0 && (
            <div className="animate-in slide-in-from-left-4 duration-500">
              <h3 className="text-[10px] uppercase tracking-widest text-black/40 mb-4 font-bold">Components</h3>
              <ul className="space-y-2">
                {data.components.map((c: any, i: number) => (
                  <li key={i} className="flex justify-between items-baseline border-b border-black/[0.03] pb-2">
                    <span className="text-[11px] font-bold uppercase">{c.name}</span>
                    <span className="text-[9px] opacity-40 italic">{c.type}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </aside>

        {/* Center: Canvas */}
        <section className="flex-1 bg-[#F9F9F9] relative flex flex-col">
          <div className="flex justify-between items-center px-8 py-3 border-b border-black/[0.03]">
             <span className="text-[9px] uppercase tracking-widest opacity-30 font-bold">Visual Manifest</span>
             {data?.diagram && (
               <button 
                 onClick={() => navigator.clipboard.writeText(data.diagram)}
                 className="text-[9px] uppercase font-bold hover:underline"
                >
                 Copy Source
               </button>
             )}
          </div>
          <div className="flex-1 overflow-auto flex items-center justify-center p-12">
            <Canvas diagram={data?.diagram} />
          </div>
        </section>

        {/* Right Side: Rationale & Scaling */}
        <aside className="w-[350px] border-l border-black/5 p-8 flex flex-col gap-10 overflow-y-auto bg-white">
          <div>
            <h3 className="text-[10px] uppercase tracking-widest text-black/40 mb-4 font-bold">Rationale</h3>
            <p className="text-[12px] leading-relaxed text-black/70">
              {data?.architecture || "Awaiting generation..."}
            </p>
          </div>

          <div className="pt-8 border-t border-black/5">
            <h3 className="text-[10px] uppercase tracking-widest text-black/40 mb-4 font-bold">Scaling</h3>
            <p className="text-[12px] leading-relaxed text-black/70">
              {data?.scaling || "Awaiting generation..."}
            </p>
          </div>

          <button 
            onClick={resetWorkspace}
            className="mt-auto text-[9px] uppercase tracking-widest text-black/20 hover:text-red-500 transition-colors font-bold text-left"
          >
            Reset Workspace
          </button>
        </aside>
      </div>
    </main>
  );
}