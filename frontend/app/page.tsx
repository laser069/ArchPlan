'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useArchitecture } from '@/hooks/useArchitecture';
import Editor from '@/components/Editor';
import Canvas from '@/components/Canvas';
import { 
  Cpu, Layers, Terminal, Box, Settings2, 
  Activity, Maximize2, Share2, HardDrive, 
  FlaskConical, Star, CheckCircle2, User as UserIcon, LogOut
} from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const { data, setData, loading, generate } = useArchitecture();
  const [provider, setProvider] = useState('groq');
  const [model, setModel] = useState('');
  const [isStarred, setIsStarred] = useState(false);
  const [userEmail, setUserEmail] = useState<string | null>(null);

  // 1. Session Protection & Setup
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }

    try {
      // Decode JWT to show user email (simple base64 decode of payload)
      const payload = JSON.parse(atob(token.split('.')[1]));
      setUserEmail(payload.sub);
    } catch (e) {
      localStorage.removeItem('access_token');
      router.push('/login');
    }

    const savedProvider = localStorage.getItem('ap_provider');
    const savedModel = localStorage.getItem('ap_model');
    if (savedProvider) setProvider(savedProvider);
    if (savedModel) setModel(savedModel);
  }, [router]);

  useEffect(() => {
    setIsStarred(false);
  }, [data]);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    router.push('/login');
  };

  const handleGenerate = (query: string, refine: boolean) => {
    localStorage.setItem('ap_provider', provider);
    localStorage.setItem('ap_model', model);
    generate(query, provider, model, refine);
  };

  const toggleGoldStandard = async () => {
    if (!data) return;
    setIsStarred(true);
    
    const token = localStorage.getItem('access_token');
    try {
      await fetch('http://localhost:8000/history/mark-gold', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
    } catch (e) {
      console.error("Gold mark failed", e);
    }
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
                <option value="ollama">Ollama</option>
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
          {/* User Session Info */}
          <div className="hidden lg:flex items-center gap-3 px-3 py-1.5 bg-white/[0.03] border border-white/5 rounded-full group">
            <UserIcon size={12} className="text-cyan-500" />
            <span className="text-[10px] font-mono text-white/50">{userEmail || '...'}</span>
            <button onClick={handleLogout} className="ml-1 text-white/20 hover:text-red-400 transition-colors">
              <LogOut size={12} />
            </button>
          </div>

          <button 
            onClick={runTest}
            className="flex items-center gap-2 px-3 py-1.5 border border-white/10 rounded text-[10px] font-mono text-white/40 hover:text-cyan-400 transition-all"
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
        </div>
      </header>

      <div className="flex-1 flex relative overflow-hidden">
        {/* LEFT PANEL */}
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
                    <div key={i} className="group bg-white/[0.02] p-3 flex justify-between items-center border border-white/5">
                      <span className="text-[11px] font-mono uppercase text-white/80">{c.name}</span>
                      <span className="text-[9px] font-mono text-white/30 uppercase">{c.type}</span>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </div>
        </div>

        {/* CENTER PANEL */}
        <div className="flex-1 bg-[#050505] relative flex flex-col overflow-hidden">
          <div className="absolute top-6 left-6 right-6 h-12 flex items-center justify-between px-6 bg-black/60 backdrop-blur-xl border border-white/10 z-30 rounded-lg">
             <span className="text-[9px] font-mono text-cyan-500 uppercase tracking-widest">Visual Logic Map</span>
             <Maximize2 size={14} className="text-white/40 hover:text-cyan-400 cursor-pointer" />
          </div>
          <div className="absolute inset-0 bg-[radial-gradient(#1a1a1a_1px,transparent_1px)] [background-size:32px_32px]">
              <Canvas data={data} />
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div className="w-[380px] bg-[#0A0A0A] border-l border-white/5 flex flex-col z-40">
          <div className="p-8 flex-1 overflow-y-auto space-y-12 custom-scrollbar">
            <section className="space-y-4">
              <div className="flex items-center gap-2 border-b border-white/5 pb-2">
                <Activity size={14} className="text-cyan-500" />
                <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/60">Architect Narrative</h2>
              </div>
              <p className="text-[12px] leading-relaxed text-white/60 font-mono italic">
                {data?.architecture || "Waiting for system description..."}
              </p>
            </section>

            <section className="space-y-4">
              <div className="flex items-center gap-2 border-b border-white/5 pb-2">
                <HardDrive size={14} className="text-cyan-500" />
                <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/60">Reliability & Scale</h2>
              </div>
              <div className="text-[11px] text-white/40 bg-white/[0.02] p-4 border border-white/5 font-mono">
                {data?.scaling || "N/A"}
              </div>
            </section>

            {data?.constraints && (
               <section className="space-y-4">
               <div className="flex items-center gap-2 border-b border-white/5 pb-2">
                 <Settings2 size={14} className="text-cyan-500" />
                 <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/60">Context</h2>
               </div>
               <div className="flex flex-wrap gap-2">
                 {Object.entries(data.constraints).map(([k, v]: [string, any]) => (
                   <div key={k} className="px-2 py-1 bg-cyan-500/5 border border-cyan-500/10 text-[9px] font-mono text-cyan-400 uppercase">
                     {k.replace(/_/g, ' ')}: {Array.isArray(v) ? v.join(', ') : String(v)}
                   </div>
                 ))}
               </div>
             </section>
            )}
          </div>
          
          <div className="p-6 border-t border-white/5 bg-black space-y-3">
            <button 
              onClick={toggleGoldStandard}
              disabled={!data || isStarred}
              className={`w-full flex items-center justify-center gap-2 py-3 border rounded-lg transition-all text-[10px] font-bold uppercase tracking-widest
                ${isStarred 
                  ? 'border-green-500/50 text-green-500 bg-green-500/5' 
                  : 'border-white/10 text-white/40 hover:border-yellow-500 hover:text-yellow-500 bg-white/[0.02]'}`}
            >
              {isStarred ? <CheckCircle2 size={14} /> : <Star size={14} />}
              {isStarred ? 'Saved for Training' : 'Mark Gold Standard'}
            </button>

            <button className="w-full bg-cyan-500 py-4 flex items-center justify-center gap-3 hover:bg-cyan-400 transition-all rounded-lg text-black font-black text-[11px] uppercase tracking-widest">
              Export Architecture <Share2 size={16} />
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}