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
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          provider,
          model,
          existing_diagram: isRefine ? data?.diagram : null,
          existing_components: isRefine ? data?.components : null,
        }),
      });

      const result = await response.json();
      setData(result);
    } catch (error) {
      console.error('Generation failed', error);
    } finally {
      setLoading(false);
    }
  };

  return { data, setData, loading, generate };
};