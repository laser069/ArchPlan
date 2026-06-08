'use client';
import { useEffect, useRef } from 'react';
import UserBubble from './UserBubble';
import AssistantBubble from './AssistantBubble';
import type { ChatMessage } from '@/hooks/useActiveChat';

interface Props {
  messages: ChatMessage[];
  loading: boolean;
}

export default function ChatThread({ messages, loading }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, loading]);

  if (messages.length === 0 && !loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center px-8">
        <div className="w-12 h-12 bg-cyan-500/10 border border-cyan-500/20 rounded-2xl flex items-center justify-center">
          <span className="text-cyan-500 text-xl">⬡</span>
        </div>
        <p className="text-[13px] font-mono text-white/30">
          Describe a system architecture to get started
        </p>
        <p className="text-[11px] font-mono text-white/15">
          Each follow-up message will refine the diagram
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto custom-scrollbar py-4 space-y-1">
      {messages.map(msg =>
        msg.role === 'user'
          ? <UserBubble key={msg.message_id} message={msg} />
          : <AssistantBubble key={msg.message_id} message={msg} />
      )}

      {loading && (
        <div className="px-4 py-2">
          <div className="flex items-center gap-3 px-4 py-3 bg-white/[0.03] border border-white/[0.08] rounded-2xl rounded-tl-sm w-fit">
            <div className="flex gap-1">
              <span className="w-1.5 h-1.5 bg-cyan-500 rounded-full animate-bounce [animation-delay:0ms]" />
              <span className="w-1.5 h-1.5 bg-cyan-500 rounded-full animate-bounce [animation-delay:150ms]" />
              <span className="w-1.5 h-1.5 bg-cyan-500 rounded-full animate-bounce [animation-delay:300ms]" />
            </div>
            <span className="text-[10px] font-mono text-cyan-400 tracking-widest">GENERATING</span>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
