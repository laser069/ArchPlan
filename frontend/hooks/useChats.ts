import { useState, useCallback } from 'react';

export interface ChatSummary {
  id: string;
  title: string;
  updated_at: string;
  message_count: number;
}

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export function useChats() {
  const [sessions, setSessions] = useState<ChatSummary[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchSessions = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/chats', { headers: authHeaders() });
      if (res.status === 401) { window.location.href = '/login'; return; }
      if (!res.ok) return;
      setSessions(await res.json());
    } finally {
      setLoading(false);
    }
  }, []);

  const createSession = useCallback(async (): Promise<string | null> => {
    const res = await fetch('/api/chats', { method: 'POST', headers: authHeaders() });
    if (res.status === 401) { window.location.href = '/login'; return null; }
    if (!res.ok) return null;
    const session = await res.json();
    setSessions(prev => [
      { id: session.id, title: session.title || 'New Chat', updated_at: session.updated_at, message_count: 0 },
      ...prev,
    ]);
    return session.id;
  }, []);

  const deleteSession = useCallback(async (id: string) => {
    const res = await fetch(`/api/chats/${id}`, { method: 'DELETE', headers: authHeaders() });
    if (res.status === 401) { window.location.href = '/login'; return; }
    if (res.ok) setSessions(prev => prev.filter(s => s.id !== id));
  }, []);

  const renameSession = useCallback(async (id: string, title: string) => {
    const res = await fetch(`/api/chats/${id}`, {
      method: 'PATCH',
      headers: authHeaders(),
      body: JSON.stringify({ title }),
    });
    if (res.status === 401) { window.location.href = '/login'; return; }
    if (res.ok) {
      setSessions(prev => prev.map(s => s.id === id ? { ...s, title } : s));
    }
  }, []);

  const updateSummary = useCallback((id: string, patch: Partial<ChatSummary>) => {
    setSessions(prev => prev.map(s => s.id === id ? { ...s, ...patch } : s));
  }, []);

  return { sessions, loading, fetchSessions, createSession, deleteSession, renameSession, updateSummary };
}
