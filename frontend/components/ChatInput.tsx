'use client';
import { useState, useRef, KeyboardEvent } from 'react';
import { Send, ChevronDown } from 'lucide-react';

interface Props {
  onSend: (content: string, provider: string, model: string) => void;
  loading: boolean;
  disabled: boolean;
}

export default function ChatInput({ onSend, loading, disabled }: Props) {
  const [content, setContent] = useState('');
  const [provider, setProvider] = useState(() => localStorage.getItem('ap_provider') || 'groq');
  const [model, setModel] = useState(() => localStorage.getItem('ap_model') || '');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = content.trim();
    if (!trimmed || loading || disabled) return;
    localStorage.setItem('ap_provider', provider);
    localStorage.setItem('ap_model', model);
    onSend(trimmed, provider, model);
    setContent('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  };

  return (
    <div className="border-t border-white/5 bg-[#0A0A0A] px-4 pt-3 pb-4 space-y-2">
      <div className="flex items-end gap-2 bg-white/[0.03] border border-white/10 rounded-2xl px-4 py-3 focus-within:border-cyan-500/40 transition-colors">
        <textarea
          ref={textareaRef}
          value={content}
          onChange={e => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={disabled ? 'Select or create a chat to start…' : 'Describe a system architecture…'}
          disabled={disabled || loading}
          rows={1}
          className="flex-1 bg-transparent text-[13px] font-mono text-white/90 placeholder-white/25 outline-none resize-none leading-relaxed"
          style={{ maxHeight: 200 }}
        />
        <button
          onClick={handleSend}
          disabled={!content.trim() || loading || disabled}
          className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-xl bg-cyan-500 text-black hover:bg-cyan-400 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
        >
          <Send size={14} />
        </button>
      </div>

      {/* Provider / model settings */}
      <div>
        <button
          onClick={() => setSettingsOpen(v => !v)}
          className="flex items-center gap-1 text-[9px] font-mono text-white/25 uppercase tracking-widest hover:text-white/50 transition-colors"
        >
          <span>{provider.toUpperCase()}{model ? ` · ${model}` : ''}</span>
          <ChevronDown size={10} className={`transition-transform ${settingsOpen ? 'rotate-180' : ''}`} />
        </button>

        {settingsOpen && (
          <div className="mt-2 flex items-center gap-6 px-2">
            <div>
              <p className="text-[9px] uppercase text-white/30 font-bold mb-1 tracking-tighter">Provider</p>
              <select
                value={provider}
                onChange={e => setProvider(e.target.value)}
                className="bg-transparent text-[11px] font-mono font-bold text-cyan-400 outline-none uppercase appearance-none cursor-pointer"
              >
                <option value="groq">Groq</option>
                <option value="openrouter">OpenRouter</option>
                <option value="gemini">Gemini</option>
                <option value="ollama">Ollama</option>
              </select>
            </div>
            <div>
              <p className="text-[9px] uppercase text-white/30 font-bold mb-1 tracking-tighter">Model Override</p>
              <input
                type="text"
                value={model}
                onChange={e => setModel(e.target.value)}
                placeholder="USE PROVIDER DEFAULT"
                className="bg-transparent text-[11px] font-mono text-white outline-none border-b border-white/10 focus:border-cyan-500 w-44 transition-all"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
