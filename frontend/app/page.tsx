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
  Settings2, 
  RefreshCcw,
  Activity,
  Maximize2,
  Share2,
  HardDrive
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
    <main className="h-screen w-full flex flex-col bg-[#050505] text-white selection:bg-cyan-500/30 font-sans">
      
      {/* HEADER */}
      <header className="h-16 border-b border-white/5 bg-black/40 backdrop-blur-xl flex items-center justify-between px-8 z-50">
        <div className="flex items-center gap-12">
          <div className="flex items-center gap-3 group">
            <div className="w-8 h-8 bg-cyan-500 flex items-center justify-center">
              <Box size={16} className="text-black" />
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-bold tracking-tighter uppercase">ArchPlan Studio</span>
              <span className="text-[10px] text-cyan-500 font-mono tracking-widest leading-none mt-1">ENGINE</span>
            </div>
          </div>
          
          <div className="h-8 w-px bg-white/10 hidden md:block" />

          {/* CONTROLS */}
          <div className="hidden md:flex items-center gap-8">
            <div className="group">
              <p className="text-[9px] uppercase text-white/40 font-bold mb-1 tracking-tighter">Provider</p>
              <select 
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="bg-transparent text-[11px] font-mono font-bold text-cyan-400 outline-none uppercase appearance-none cursor-pointer"
              >
                <option value="groq">Groq</option>
                <option value="openrouter">OpenRouter</option>
                <option value="gemini">Gemini</option>
              </select>
            </div>

            <div className="group">
              <p className="text-[9px] uppercase text-white/40 font-bold mb-1 tracking-tighter">Model</p>
              <input 
                type="text" 
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="NOT DEFINED"
                className="bg-transparent text-[11px] font-mono text-white outline-none border-b border-white/10 focus:border-cyan-500 w-44 transition-all"
              />
            </div>
          </div>
        </div>

        <div className="flex items-center gap-6">
          {loading && (
            <div className="flex items-center gap-3 px-4 py-2 bg-cyan-500/10 border border-cyan-500/20 animate-pulse">
              <Activity size={12} className="text-cyan-400" />
              <span className="text-[10px] font-mono text-cyan-400 font-bold">GENERATING</span>
            </div>
          )}
          <button className="text-white/40 hover:text-white transition-colors">
            <Settings2 size={18} />
          </button>
        </div>
      </header>

      <div className="flex-1 flex relative overflow-hidden">
        
        {/* LEFT PANEL */}
        <div className="w-[420px] bg-[#0A0A0A] border-r border-white/5 flex flex-col z-40">
          <div className="p-8 flex-1 overflow-y-auto space-y-10 custom-scrollbar">
            <section>
              <div className="flex items-center gap-2 mb-6 border-b border-white/5 pb-2">
                <Terminal size={14} className="text-cyan-500" />
                <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/60">Input</h2>
              </div>
              <Editor onGenerate={handleGenerate} loading={loading} hasDiagram={!!data?.diagram} />
            </section>
            
            {data?.components && (
              <section className="animate-in fade-in slide-in-from-bottom-4 duration-700">
                <div className="flex items-center gap-2 mb-6 border-b border-white/5 pb-2">
                  <Layers size={14} className="text-cyan-500" />
                  <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/60">Inventory</h2>
                </div>
                <div className="grid grid-cols-1 gap-1">
                  {data.components.map((c: any, i: number) => (
                    <div key={i} className="group bg-white/[0.02] hover:bg-white/[0.05] p-3 flex justify-between items-center transition-all border border-white/5">
                      <div className="flex items-center gap-3">
                        <div className="w-1.5 h-1.5 bg-cyan-500/40 group-hover:bg-cyan-500" />
                        <span className="text-[11px] font-mono uppercase tracking-tight text-white/80">{c.name}</span>
                      </div>
                      <span className="text-[9px] font-mono text-white/30 group-hover:text-cyan-500 transition-colors uppercase">{c.type}</span>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </div>
        </div>

        {/* CENTER VIEWPORT */}
        <div className="flex-1 bg-[#050505] relative flex flex-col overflow-hidden">
          <div className="absolute top-6 left-6 right-6 h-12 flex items-center justify-between px-6 bg-black/60 backdrop-blur-xl border border-white/10 z-30">
            <div className="flex items-center gap-4">
              <span className="text-[9px] font-mono text-cyan-500 uppercase tracking-widest">Canvas View</span>
              <div className="w-2 h-2 rounded-full bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.8)]" />
            </div>
            <div className="flex items-center gap-4">
              <button onClick={() => navigator.clipboard.writeText(data?.diagram || '')} className="text-[10px] font-mono text-white/40 hover:text-cyan-400 transition-colors uppercase">Copy Code</button>
              <Maximize2 size={14} className="text-white/40 cursor-pointer" />
            </div>
          </div>

          <div className="flex-1 flex items-center justify-center p-20 bg-[radial-gradient(#1a1a1a_1px,transparent_1px)] [background-size:32px_32px]">
             <Canvas diagram={data?.diagram} />
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div className="w-[360px] bg-[#0A0A0A] border-l border-white/5 flex flex-col z-40">
          <div className="p-8 flex-1 overflow-y-auto space-y-12 custom-scrollbar">
            <section className="space-y-4">
              <div className="flex items-center gap-2 border-b border-white/5 pb-2">
                <Activity size={14} className="text-cyan-500" />
                <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/60">Rationale</h2>
              </div>
              <p className="text-[12px] leading-relaxed text-white/60 font-mono italic">
                {data?.architecture || "Awaiting input..."}
              </p>
            </section>

            <section className="space-y-4">
              <div className="flex items-center gap-2 border-b border-white/5 pb-2">
                <HardDrive size={14} className="text-cyan-500" />
                <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/60">Scaling</h2>
              </div>
              <div className="text-[11px] leading-relaxed text-white/40 bg-white/[0.02] p-4 border border-white/5 font-mono">
                {data?.scaling || "No assessment."}
              </div>
            </section>
          </div>
          
          <div className="p-8 border-t border-white/5 bg-black">
            <button className="group w-full bg-cyan-500 py-4 flex items-center justify-center gap-3 hover:bg-cyan-400 transition-all overflow-hidden relative">
              <span className="text-[11px] font-black text-black uppercase tracking-widest relative z-10">Export Blueprint</span>
              <Share2 size={16} className="text-black relative z-10" />
              <div className="absolute inset-0 bg-white transform translate-y-full group-hover:translate-y-0 transition-transform duration-300 opacity-20" />
            </button>
          </div>
        </div>
      </div>

      {/* FOOTER */}
      <footer className="h-8 border-t border-white/5 bg-black px-6 flex items-center justify-between z-50">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className={`w-1.5 h-1.5 rounded-full ${loading ? 'bg-cyan-500 animate-ping' : 'bg-green-500'}`} />
            <span className="text-[8px] font-mono text-white/40 uppercase tracking-widest">{loading ? 'Active' : 'Ready'}</span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-[9px] font-mono text-white/20 uppercase">ArchPlan Studio</span>
        </div>
      </footer>
    </main>
  );
}