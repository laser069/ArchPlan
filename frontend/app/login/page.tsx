'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Box, Lock, Mail, ArrowRight, Loader2 } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // REQUIRED: Form-data encoding for OAuth2PasswordRequestForm
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    try {
      const res = await fetch('http://localhost:8000/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      });

      if (!res.ok) throw new Error('Invalid credentials');
      
      const data = await res.json();
      localStorage.setItem('access_token', data.access_token);
      router.push('/');
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
          <div className="w-12 h-12 bg-cyan-500 flex items-center justify-center">
            <Box size={24} className="text-black" />
          </div>
          <h1 className="text-xl font-black uppercase tracking-[0.2em]">ArchPlan Login</h1>
          <p className="text-[10px] font-mono text-white/40 uppercase tracking-widest">Secure Neural Access</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div className="space-y-1">
            <div className="relative group">
              <Mail className="absolute left-4 top-4 text-white/20 group-focus-within:text-cyan-500 transition-colors" size={16} />
              <input 
                type="email" required placeholder="EMAIL_ADDRESS"
                value={email} onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-white/[0.03] border border-white/10 p-4 pl-12 text-sm font-mono text-white focus:border-cyan-500 outline-none transition-all"
              />
            </div>
          </div>

          <div className="space-y-1">
            <div className="relative group">
              <Lock className="absolute left-4 top-4 text-white/20 group-focus-within:text-cyan-500 transition-colors" size={16} />
              <input 
                type="password" required placeholder="ACCESS_KEY"
                value={password} onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-white/[0.03] border border-white/10 p-4 pl-12 text-sm font-mono text-white focus:border-cyan-500 outline-none transition-all"
              />
            </div>
          </div>

          {error && <p className="text-[10px] font-mono text-red-500 uppercase text-center">{error}</p>}

          <button 
            disabled={loading}
            className="w-full bg-cyan-500 hover:bg-cyan-400 text-black font-black py-4 flex items-center justify-center gap-2 transition-all uppercase tracking-widest text-xs"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <>Initialize Engine <ArrowRight size={16} /></>}
          </button>
        </form>

        <p className="text-center text-[10px] font-mono text-white/30 uppercase tracking-widest">
          No access? <Link href="/signup" className="text-cyan-500 hover:underline">Register Identity</Link>
        </p>
      </div>
    </div>
  );
}