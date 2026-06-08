'use client';
import { useState } from 'react';
import { Plus, Trash2, MessageSquare, LogOut, User as UserIcon } from 'lucide-react';
import type { ChatSummary } from '@/hooks/useChats';

interface Props {
  sessions: ChatSummary[];
  activeId: string | null;
  loading: boolean;
  userEmail: string | null;
  onNewChat: () => void;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onLogout: () => void;
}

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function Sidebar({
  sessions, activeId, loading, userEmail,
  onNewChat, onSelect, onDelete, onLogout,
}: Props) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  return (
    <div className="w-[260px] flex-shrink-0 bg-[#080808] border-r border-white/5 flex flex-col h-full">
      {/* Logo */}
      <div className="px-4 pt-5 pb-4 border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-cyan-500 flex items-center justify-center rounded-sm">
            <span className="text-black font-black text-[11px]">AP</span>
          </div>
          <div>
            <p className="text-[11px] font-bold tracking-tight uppercase text-white">ArchPlan</p>
            <p className="text-[9px] font-mono text-cyan-500 tracking-widest leading-none">STUDIO</p>
          </div>
        </div>
      </div>

      {/* New Chat */}
      <div className="px-3 py-3">
        <button
          onClick={onNewChat}
          className="w-full flex items-center gap-2 px-3 py-2.5 bg-cyan-500/10 border border-cyan-500/20 rounded-xl text-[11px] font-mono text-cyan-400 hover:bg-cyan-500/20 hover:text-cyan-300 transition-all"
        >
          <Plus size={13} />
          New Chat
        </button>
      </div>

      {/* Session list */}
      <div className="flex-1 overflow-y-auto custom-scrollbar px-2 space-y-0.5">
        {loading && sessions.length === 0 && (
          <p className="text-[10px] font-mono text-white/20 text-center py-8">Loading…</p>
        )}
        {!loading && sessions.length === 0 && (
          <p className="text-[10px] font-mono text-white/20 text-center py-8">No chats yet</p>
        )}
        {sessions.map(s => (
          <div
            key={s.id}
            onMouseEnter={() => setHoveredId(s.id)}
            onMouseLeave={() => setHoveredId(null)}
            onClick={() => onSelect(s.id)}
            className={`group relative flex items-start gap-2 px-3 py-2.5 rounded-xl cursor-pointer transition-all ${
              s.id === activeId
                ? 'bg-white/[0.08] border border-white/10'
                : 'hover:bg-white/[0.04]'
            }`}
          >
            <MessageSquare size={11} className="mt-0.5 flex-shrink-0 text-white/25" />
            <div className="flex-1 min-w-0">
              <p className="text-[11px] font-mono text-white/70 truncate leading-tight">
                {s.title || 'New Chat'}
              </p>
              <p className="text-[9px] font-mono text-white/25 mt-0.5">
                {relativeTime(s.updated_at)} · {s.message_count} msg{s.message_count !== 1 ? 's' : ''}
              </p>
            </div>
            {hoveredId === s.id && (
              <button
                onClick={e => { e.stopPropagation(); onDelete(s.id); }}
                className="flex-shrink-0 p-1 text-white/20 hover:text-red-400 transition-colors rounded"
              >
                <Trash2 size={11} />
              </button>
            )}
          </div>
        ))}
      </div>

      {/* User footer */}
      <div className="px-3 py-3 border-t border-white/5">
        <div className="flex items-center gap-2 px-2 py-2 rounded-xl bg-white/[0.02]">
          <UserIcon size={11} className="text-cyan-500 flex-shrink-0" />
          <span className="flex-1 text-[10px] font-mono text-white/40 truncate">{userEmail || '…'}</span>
          <button onClick={onLogout} className="text-white/20 hover:text-red-400 transition-colors">
            <LogOut size={11} />
          </button>
        </div>
      </div>
    </div>
  );
}
