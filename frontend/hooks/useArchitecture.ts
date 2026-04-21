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

    try {
      const response = await fetch('http://localhost:8000/generate', { // Points to your FastAPI
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          provider,
          model: model || undefined,
          // If refining, send the previous state
          existing_diagram: isRefine ? { nodes: data.nodes, edges: data.edges } : null,
          existing_components: isRefine ? data.components : null,
          // Send back the constraints the backend extracted last time
          cached_constraints: data?.constraints || null, 
        }),
      });

      const result = await response.json();
      
      // If we are refining, we might want to keep the old constraints 
      // if the backend didn't return new ones
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