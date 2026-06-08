'use client';
import type { ChatMessage } from '@/hooks/useActiveChat';

interface Props { message: ChatMessage; }

export default function UserBubble({ message }: Props) {
  return (
    <div className="flex justify-end px-4 py-2">
      <div className="max-w-[75%] bg-cyan-500/10 border border-cyan-500/20 rounded-2xl rounded-tr-sm px-4 py-3">
        <p className="text-[13px] font-mono text-white/90 whitespace-pre-wrap leading-relaxed">
          {message.content}
        </p>
      </div>
    </div>
  );
}
