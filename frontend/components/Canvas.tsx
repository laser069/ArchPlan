'use client';
import { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

// Initialize with 'base' to allow CSS overrides
mermaid.initialize({
  startOnLoad: false,
  theme: 'base',
  themeVariables: {
    fontFamily: 'var(--font-sans)',
    fontSize: '14px',
    primaryColor: '#ffffff',
    lineColor: '#000000',
  },
  flowchart: { 
    useMaxWidth: false, // Prevents Mermaid from forcing a fixed width
    htmlLabels: true,
    curve: 'linear' 
  }
});

export default function Canvas({ diagram }: { diagram: string }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (diagram && containerRef.current) {
      containerRef.current.innerHTML = '';
      const id = `svg-${Math.random().toString(36).substr(2, 9)}`;
      
      const render = async () => {
        try {
          const { svg } = await mermaid.render(id, diagram);
          if (containerRef.current) {
            containerRef.current.innerHTML = svg;
            
            // Force the SVG to be responsive via DOM manipulation
            const svgElement = containerRef.current.querySelector('svg');
            if (svgElement) {
              svgElement.style.maxWidth = '100%';
              svgElement.style.height = 'auto';
              svgElement.style.width = '100%';
            }
          }
        } catch (e) {
          console.error("Render failed", e);
        }
      };
      render();
    }
  }, [diagram]);

  return (
    <div className="w-full h-full min-h-[500px] flex items-center justify-center bg-grid-pattern overflow-hidden">
      {!diagram ? (
        <p className="text-[10px] uppercase tracking-widest opacity-20">Awaiting Generation</p>
      ) : (
        <div 
          ref={containerRef} 
          className="w-full h-full p-8 overflow-auto flex items-center justify-center transition-opacity duration-500 animate-in fade-in" 
        />
      )}
    </div>
  );
}