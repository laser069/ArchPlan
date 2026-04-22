'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Box, ShieldPlus, Loader2 } from 'lucide-react';

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await fetch(`http://localhost:8000/signup?email=${email}&password=${password}`, {
        method: 'POST',
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Registration failed');
      }

      router.push('/login?registered=true');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center p-4">
      <div className="w-full max-w-[400px] space-y-8">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border border-cyan-500/50 flex items-center justify-center">
            <Box size={24} className="text-cyan-500" />
          </div>
          <h1 className="text-xl font-black uppercase tracking-[0.2em]">New Identity</h1>
          <p className="text-[10px] font-mono text-white/40 uppercase tracking-widest">Register Architecture Node</p>
        </div>

        <form onSubmit={handleSignup} className="space-y-4">
          <input 
            type="email" required placeholder="EMAIL_ADDRESS"
            value={email} onChange={(e) => setEmail(e.target.value)}
            className="w-full bg-transparent border border-white/10 p-4 text-sm font-mono text-white focus:border-cyan-500 outline-none transition-all"
          />
          <input 
            type="password" required placeholder="CREATE_ACCESS_KEY"
            value={password} onChange={(e) => setPassword(e.target.value)}
            className="w-full bg-transparent border border-white/10 p-4 text-sm font-mono text-white focus:border-cyan-500 outline-none transition-all"
          />

          {error && <p className="text-[10px] font-mono text-red-500 uppercase text-center">{error}</p>}

          <button 
            disabled={loading}
            className="w-full border border-cyan-500 text-cyan-500 hover:bg-cyan-500 hover:text-black font-black py-4 flex items-center justify-center gap-2 transition-all uppercase tracking-widest text-xs"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <>Create Account <ShieldPlus size={16} /></>}
          </button>
        </form>

        <p className="text-center text-[10px] font-mono text-white/30 uppercase tracking-widest">
          Have identity? <Link href="/login" className="text-cyan-500 hover:underline">Access Engine</Link>
        </p>
      </div>
    </div>
  );
}