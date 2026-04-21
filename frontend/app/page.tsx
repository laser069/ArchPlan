'use client';

import { useState, useEffect } from 'react';
import { useArchitecture } from '@/hooks/useArchitecture';
import Editor from '@/components/Editor';
import Canvas from '@/components/Canvas';
import { 
  Cpu, Layers, Terminal, Box, Settings2, 
  RefreshCcw, Activity, Maximize2, Share2, HardDrive, 
  FlaskConical, Star, CheckCircle2
} from 'lucide-react';

export default function Home() {
  const { data, setData, loading, generate } = useArchitecture();
  const [provider, setProvider] = useState('groq');
  const [model, setModel] = useState('');
  const [isStarred, setIsStarred] = useState(false);

  // Sync settings with LocalStorage
  useEffect(() => {
    const savedProvider = localStorage.getItem('ap_provider');
    const savedModel = localStorage.getItem('ap_model');
    if (savedProvider) setProvider(savedProvider);
    if (savedModel) setModel(savedModel);
  }, []);

  // Reset star status when new data arrives
  useEffect(() => {
    setIsStarred(false);
  }, [data]);

  const handleGenerate = (query: string, refine: boolean) => {
    localStorage.setItem('ap_provider', provider);
    localStorage.setItem('ap_model', model);
    generate(query, provider, model, refine);
  };

  const toggleGoldStandard = async () => {
    // This tags the current architecture in your MongoDB for fine-tuning
    if (!data) return;
    
    setIsStarred(true);
    console.log("Marking as Gold Standard for Fine-Tuning dataset...");
    
    // Optional: add a specific fetch call to update the DB record if you return IDs
    // await fetch(`http://localhost:8000/admin/mark-gold/${data.id}`, { method: 'POST' });
  };

  const runTest = async () => {
    try {
      const res = await fetch('http://localhost:8000/test-diagram');
      const testData = await res.json();
      if (setData) setData(testData); 
    } catch (e) {
      console.error("Test endpoint failed.", e);
    }
  };

  return (
    <main className="h-screen w-full flex flex-col bg-[#050505] text-white selection:bg-cyan-500/30 font-sans">
      
      {/* HEADER */}
      <header className="h-16 border-b border-white/5 bg-black/40 backdrop-blur-xl flex items-center justify-between px-8 z-50">
        <div className="flex items-center gap-12">
          <div className="flex items-center gap-3 group cursor-pointer" onClick={() => window.location.reload()}>
            <div className="w-8 h-8 bg-cyan-500 flex items-center justify-center">
              <Box size={16} className="text-black" />
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-bold tracking-tighter uppercase">ArchPlan Studio</span>
              <span className="text-[10px] text-cyan-500 font-mono tracking-widest leading-none mt-1">ENGINE</span>
            </div>
          </div>
          
          <div className="h-8 w-px bg-white/10 hidden md:block" />

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
                <option value="ollama">Ollama (Local)</option>
              </select>
            </div>

            <div className="group">
              <p className="text-[9px] uppercase text-white/40 font-bold mb-1 tracking-tighter">Model Override</p>
              <input 
                type="text" 
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="USE PROVIDER DEFAULT"
                className="bg-transparent text-[11px] font-mono text-white outline-none border-b border-white/10 focus:border-cyan-500 w-44 transition-all"
              />
            </div>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <button 
            onClick={runTest}
            className="flex items-center gap-2 px-3 py-1.5 border border-white/10 rounded text-[10px] font-mono text-white/40 hover:text-cyan-400 hover:border-cyan-500/50 transition-all"
          >
            <FlaskConical size={12} />
            DEV_TEST
          </button>

          {loading && (
            <div className="flex items-center gap-3 px-4 py-2 bg-cyan-500/10 border border-cyan-500/20 animate-pulse">
              <Activity size={12} className="text-cyan-400" />
              <span className="text-[10px] font-mono text-cyan-400 font-bold tracking-widest">PROCESSING</span>
            </div>
          )}
          <button className="text-white/40 hover:text-white transition-colors">
            <Settings2 size={18} />
          </button>
        </div>
      </header>

      <div className="flex-1 flex relative overflow-hidden">
        
        {/* LEFT PANEL: INPUT & INVENTORY */}
        <div className="w-[420px] bg-[#0A0A0A] border-r border-white/5 flex flex-col z-40">
          <div className="p-8 flex-1 overflow-y-auto space-y-10 custom-scrollbar">
            <section>
              <div className="flex items-center gap-2 mb-6 border-b border-white/5 pb-2">
                <Terminal size={14} className="text-cyan-500" />
                <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/60">Architectural Query</h2>
              </div>
              <Editor onGenerate={handleGenerate} loading={loading} hasDiagram={!!data?.nodes} />
            </section>
            
            {data?.components && (
              <section className="animate-in fade-in slide-in-from-bottom-4 duration-700">
                <div className="flex items-center gap-2 mb-6 border-b border-white/5 pb-2">
                  <Layers size={14} className="text-cyan-500" />
                  <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/60">Infrastructure Nodes</h2>
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

        {/* CENTER PANEL: CANVAS */}
        <div className="flex-1 bg-[#050505] relative flex flex-col overflow-hidden">
          <div className="absolute top-6 left-6 right-6 h-12 flex items-center justify-between px-6 bg-black/60 backdrop-blur-xl border border-white/10 z-30 rounded-lg">
            <div className="flex items-center gap-4">
              <span className="text-[9px] font-mono text-cyan-500 uppercase tracking-widest">Visual Logic Map</span>
              <div className="w-2 h-2 rounded-full bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.8)]" />
            </div>
            <div className="flex items-center gap-4">
              <button 
                onClick={() => navigator.clipboard.writeText(JSON.stringify(data || {}))} 
                className="text-[10px] font-mono text-white/40 hover:text-cyan-400 transition-colors uppercase"
              >
                Copy Full State
              </button>
              <div className="h-4 w-px bg-white/10 mx-2" />
              <Maximize2 size={14} className="text-white/40 hover:text-cyan-400 cursor-pointer transition-colors" />
            </div>
          </div>

          <div className="absolute inset-0 top-0 bg-[radial-gradient(#1a1a1a_1px,transparent_1px)] [background-size:32px_32px]">
              <Canvas data={data} />
          </div>
        </div>

        {/* RIGHT PANEL: ANALYSIS & FEEDBACK */}
        <div className="w-[380px] bg-[#0A0A0A] border-l border-white/5 flex flex-col z-40">
          <div className="p-8 flex-1 overflow-y-auto space-y-12 custom-scrollbar">
            <section className="space-y-4">
              <div className="flex items-center gap-2 border-b border-white/5 pb-2">
                <Activity size={14} className="text-cyan-500" />
                <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/60">Architect Narrative</h2>
              </div>
              <p className="text-[12px] leading-relaxed text-white/60 font-mono italic">
                {data?.architecture || "Waiting for system description to analyze patterns..."}
              </p>
            </section>

            <section className="space-y-4">
              <div className="flex items-center gap-2 border-b border-white/5 pb-2">
                <HardDrive size={14} className="text-cyan-500" />
                <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/60">Reliability & Scale</h2>
              </div>
              <div className="text-[11px] leading-relaxed text-white/40 bg-white/[0.02] p-4 border border-white/5 font-mono">
                {data?.scaling || "Performance assessment will appear here."}
              </div>
            </section>

            {data?.constraints && (
               <section className="space-y-4">
               <div className="flex items-center gap-2 border-b border-white/5 pb-2">
                 <Settings2 size={14} className="text-cyan-500" />
                 <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/60">Extracted Context</h2>
               </div>
               <div className="flex flex-wrap gap-2">
                 {Object.entries(data.constraints).map(([k, v]: [string, any]) => (
                   <div key={k} className="px-2 py-1 bg-cyan-500/5 border border-cyan-500/10 rounded text-[9px] font-mono text-cyan-400">
                     {k.replace(/_/g, ' ')}: {Array.isArray(v) ? v.join(', ') : v}
                   </div>
                 ))}
               </div>
             </section>
            )}
          </div>
          
          <div className="p-6 border-t border-white/5 bg-black space-y-3">
            <div className="flex gap-2">
              <button 
                onClick={toggleGoldStandard}
                disabled={!data || isStarred}
                className={`flex-1 flex items-center justify-center gap-2 py-3 border rounded-lg transition-all text-[10px] font-bold uppercase tracking-widest
                  ${isStarred 
                    ? 'border-green-500/50 text-green-500 bg-green-500/5' 
                    : 'border-white/10 text-white/40 hover:border-yellow-500/50 hover:text-yellow-500 bg-white/[0.02]'}`}
              >
                {isStarred ? <CheckCircle2 size={14} /> : <Star size={14} />}
                {isStarred ? 'Saved for Training' : 'Mark Gold Standard'}
              </button>
            </div>

            <button className="group w-full bg-cyan-500 py-4 flex items-center justify-center gap-3 hover:bg-cyan-400 transition-all overflow-hidden relative rounded-lg">
              <span className="text-[11px] font-black text-black uppercase tracking-widest relative z-10">Export Architecture</span>
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
            <span className="text-[8px] font-mono text-white/40 uppercase tracking-widest">{loading ? 'Engine Active' : 'System Standby'}</span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-[9px] font-mono text-white/10 uppercase tracking-[0.3em]">ArchPlan Neural v1.0</span>
        </div>
      </footer>
    </main>
  );
}