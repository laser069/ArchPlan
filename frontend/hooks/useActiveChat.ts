import { useState, useCallback } from 'react';

export interface DiagramSnapshot {
  nodes: any[];
  edges: any[];
  raw_nodes: string[][];
  raw_edges: string[][];
  components: { name: string; type: string }[];
}

export interface ChatMessage {
  message_id: string;
  role: 'user' | 'assistant';
  content: string;
  diagram?: DiagramSnapshot;
  scaling?: string;
  constraints?: Record<string, any>;
  provider?: string;
  model_name?: string;
  created_at: string;
}

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export function useActiveChat(onSummaryUpdate?: (id: string, title: string, count: number) => void) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSession = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/chats/${id}`, { headers: authHeaders() });
      if (res.status === 401) { window.location.href = '/login'; return; }
      if (!res.ok) { setError('Failed to load chat'); return; }
      const session = await res.json();
      setSessionId(id);
      setMessages(session.messages ?? []);
    } finally {
      setLoading(false);
    }
  }, []);

  const clearSession = useCallback(() => {
    setSessionId(null);
    setMessages([]);
    setError(null);
  }, []);

  const sendMessage = useCallback(async (
    id: string,
    content: string,
    provider: string,
    model: string,
  ) => {
    setLoading(true);
    setError(null);

    // Optimistic user bubble
    const optimisticMsg: ChatMessage = {
      message_id: `opt-${Date.now()}`,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, optimisticMsg]);

    try {
      const res = await fetch(`/api/chats/${id}/messages`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ content, provider, model: model || undefined }),
      });

      if (res.status === 401) { window.location.href = '/login'; return; }

      if (!res.ok) {
        // Roll back optimistic message on error
        setMessages(prev => prev.filter(m => m.message_id !== optimisticMsg.message_id));
        const err = await res.json().catch(() => null);
        setError(err?.detail || err?.error || 'Generation failed');
        return;
      }

      const session = await res.json();
      setSessionId(id);
      setMessages(session.messages ?? []);

      onSummaryUpdate?.(id, session.title, session.messages?.length ?? 0);
    } catch (e: any) {
      setMessages(prev => prev.filter(m => m.message_id !== optimisticMsg.message_id));
      setError(e?.message || 'Generation failed');
    } finally {
      setLoading(false);
    }
  }, [onSummaryUpdate]);

  return { sessionId, setSessionId, messages, loading, error, loadSession, clearSession, sendMessage };
}
