import { useState } from 'react';

export const useArchitecture = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = async (
    query: string,
    provider: string,
    model: string,
    isRefine: boolean
  ) => {
    setLoading(true);
    setError(null);

    // 1. Retrieve the token from storage (localStorage/sessionStorage)
    const token = localStorage.getItem('access_token');

    // Guard against missing token: avoid sending "Authorization: Bearer null"
    if (!token) {
      console.error('No access token found. Please log in again.');
      setLoading(false);
      setError('No access token. Please log in.');
      return;
    }

    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || '/api/generate';
      const response = await fetch(backendUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // 2. Attach the Bearer Token
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          query,
          provider,
          model: model || undefined,
          existing_diagram: (isRefine && data) ? { nodes: data.nodes, edges: data.edges } : null,
          existing_components: isRefine ? (data?.components ?? null) : null,
          cached_constraints: data?.constraints || null, 
        }),
      });

      // 3. Handle Unauthorized (Token expired or missing)
      if (response.status === 401) {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
        return;
      }

      if (!response.ok) {
        const errBody = await response.json().catch(() => null);
        const detail = errBody?.detail || errBody?.error || response.statusText;
        throw new Error(`Server error: ${detail}`);
      }

      const result = await response.json();

      setData(result);
    } catch (error) {
      console.error('Generation failed', error);
      setError(error instanceof Error ? error.message : 'Generation failed');
    } finally {
      setLoading(false);
    }
  };

  return { data, setData, loading, generate, error };
};