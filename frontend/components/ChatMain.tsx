'use client';
import ChatThread from './ChatThread';
import ChatInput from './ChatInput';
import type { ChatMessage } from '@/hooks/useActiveChat';

interface Props {
  messages: ChatMessage[];
  loading: boolean;
  sessionId: string | null;
  onSend: (content: string, provider: string, model: string) => void;
}

export default function ChatMain({ messages, loading, sessionId, onSend }: Props) {
  return (
    <div className="flex-1 flex flex-col min-h-0">
      <ChatThread messages={messages} loading={loading} />
      <ChatInput onSend={onSend} loading={loading} disabled={!sessionId} />
    </div>
  );
}
