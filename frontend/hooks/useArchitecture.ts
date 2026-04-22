import { useState } from 'react';

export const useArchitecture = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const generate = async (
    query: string,
    provider: string,
    model: string,
    isRefine: boolean
  ) => {
    setLoading(true);

    // 1. Retrieve the token from storage (localStorage/sessionStorage)
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch('http://localhost:8000/generate', {
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
          existing_diagram: isRefine ? { nodes: data?.nodes, edges: data?.edges } : null,
          existing_components: isRefine ? data?.components : null,
          cached_constraints: data?.constraints || null, 
        }),
      });

      // 3. Handle Unauthorized (Token expired or missing)
      if (response.status === 401) {
        console.error("Session expired. Please log in again.");
        // Optional: window.location.href = '/login';
        return;
      }

      if (!response.ok) {
        throw new Error(`Server error: ${response.statusText}`);
      }

      const result = await response.json();
      
      if (isRefine && !result.constraints && data?.constraints) {
        result.constraints = data.constraints;
      }

      setData(result);
    } catch (error) {
      console.error('Generation failed', error);
    } finally {
      setLoading(false);
    }
  };

  return { data, setData, loading, generate };
};