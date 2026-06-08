'use client';
import { useEffect, useCallback } from 'react';
import Sidebar from './Sidebar';
import ChatMain from './ChatMain';
import { useChats } from '@/hooks/useChats';
import { useActiveChat } from '@/hooks/useActiveChat';

interface Props {
  userEmail: string | null;
  onLogout: () => void;
}

export default function ChatLayout({ userEmail, onLogout }: Props) {
  const {
    sessions, loading: sessionsLoading,
    fetchSessions, createSession, deleteSession, updateSummary,
  } = useChats();

  const handleSummaryUpdate = useCallback((id: string, title: string, count: number) => {
    updateSummary(id, { title: title || 'New Chat', message_count: count, updated_at: new Date().toISOString() });
  }, [updateSummary]);

  const {
    sessionId, setSessionId, messages, loading: chatLoading, loadSession, clearSession, sendMessage,
  } = useActiveChat(handleSummaryUpdate);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const handleNewChat = async () => {
    const id = await createSession();
    if (id) {
      clearSession();
      setSessionId(id);
    }
  };

  const handleSelectSession = async (id: string) => {
    if (id === sessionId) return;
    await loadSession(id);
  };

  const handleDeleteSession = async (id: string) => {
    await deleteSession(id);
    if (id === sessionId) clearSession();
  };

  const handleSend = async (content: string, provider: string, model: string) => {
    if (!sessionId) return;
    await sendMessage(sessionId, content, provider, model);
  };

  return (
    <div className="h-screen w-full flex bg-[#050505] text-white font-sans overflow-hidden">
      <Sidebar
        sessions={sessions}
        activeId={sessionId}
        loading={sessionsLoading}
        userEmail={userEmail}
        onNewChat={handleNewChat}
        onSelect={handleSelectSession}
        onDelete={handleDeleteSession}
        onLogout={onLogout}
      />
      <ChatMain
        messages={messages}
        loading={chatLoading}
        sessionId={sessionId}
        onSend={handleSend}
      />
    </div>
  );
}
