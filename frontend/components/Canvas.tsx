'use client';
import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import { ZoomIn, ZoomOut, Maximize, Minimize } from 'lucide-react';

export default function Canvas({ diagram }: { diagram: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svgDimensions, setSvgDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const accent = isDarkMode ? '#3b82f6' : '#2563eb'; 
    const text = isDarkMode ? '#fafafa' : '#09090b';
    const bg = isDarkMode ? '#09090b' : '#ffffff';

    mermaid.initialize({
      startOnLoad: false,
      theme: 'base',
      themeVariables: {
        fontFamily: 'var(--font-geist-mono)',
        fontSize: '16px', // Increased from 13px
        primaryColor: isDarkMode ? '#18181b' : '#f4f4f5',
        primaryTextColor: text,
        primaryBorderColor: accent,
        lineColor: isDarkMode ? '#3f3f46' : '#d4d4d8',
        nodeBorder: accent,
        tertiaryColor: isDarkMode ? '#18181b' : '#f4f4f5',
        edgeLabelBackground: bg,
        mainBkg: isDarkMode ? '#18181b' : '#f4f4f5',
        secondaryColor: isDarkMode ? '#27272a' : '#e4e4e7',
        tertiaryBorderColor: accent,
      },
      flowchart: { 
        curve: 'basis', // Changed from 'linear' for smoother curves
        padding: 60, // Increased padding
        nodeSpacing: 80, // Add more space between nodes
        rankSpacing: 100, // Add more space between ranks
        diagramPadding: 40,
        htmlLabels: true,
      },
      // Increase diagram scale
      gantt: { fontSize: 16 },
      sequence: { fontSize: 16 },
      class: { fontSize: 16 },
    });

    if (diagram && containerRef.current) {
      const id = `svg-${Math.random().toString(36).substring(2, 11)}`;
      const render = async () => {
        try {
          const cleanDiagram = diagram.replace(/```mermaid/g, '').replace(/```/g, '').trim();
          const { svg } = await mermaid.render(id, cleanDiagram);
          if (containerRef.current) {
            containerRef.current.innerHTML = svg;
            const svgElement = containerRef.current.querySelector('svg');
            if (svgElement) {
              // Remove fixed dimensions to allow scaling
              svgElement.removeAttribute('height');
              svgElement.removeAttribute('width');
              
              // Get viewBox dimensions
              const viewBox = svgElement.getAttribute('viewBox');
              if (viewBox) {
                const [, , width, height] = viewBox.split(' ').map(Number);
                setSvgDimensions({ width, height });
              }
              
              // Set responsive sizing
              svgElement.style.maxWidth = 'none';
              svgElement.style.width = 'auto';
              svgElement.style.height = 'auto';
              
              // Make text and shapes more interactive
              const nodes = svgElement.querySelectorAll('.node, .nodeLabel, .edgeLabel');
              nodes.forEach(node => {
                (node as HTMLElement).style.cursor = 'pointer';
              });
            }
          }
        } catch (e) {
          console.error("Render_Error", e);
        }
      };
      render();
    }
  }, [diagram]);

  return (
    <div className="relative w-full h-full bg-blueprint overflow-hidden">
      <TransformWrapper
        initialScale={0.8}
        minScale={0.1}
        maxScale={5}
        centerOnInit={true}
        wheel={{ step: 0.1 }}
        doubleClick={{ mode: "reset" }}
        panning={{ velocityDisabled: false }}
      >
        {({ zoomIn, zoomOut, resetTransform, centerView }) => (
          <>
            {/* FLOATING CONTROLS */}
            <div className="absolute bottom-6 right-6 flex flex-col gap-2 z-30">
              <button 
                onClick={() => zoomIn(0.3)} 
                className="p-3 bg-background border border-border hover:bg-accent hover:text-white hover:border-accent transition-all shadow-xl group"
                title="Zoom In"
              >
                <ZoomIn size={18} className="group-hover:scale-110 transition-transform" />
              </button>
              <button 
                onClick={() => zoomOut(0.3)} 
                className="p-3 bg-background border border-border hover:bg-accent hover:text-white hover:border-accent transition-all shadow-xl group"
                title="Zoom Out"
              >
                <ZoomOut size={18} className="group-hover:scale-110 transition-transform" />
              </button>
              <button 
                onClick={() => {
                  resetTransform();
                  centerView(0.8);
                }} 
                className="p-3 bg-background border border-border hover:bg-accent hover:text-white hover:border-accent transition-all shadow-xl group"
                title="Reset View"
              >
                <Maximize size={18} className="group-hover:scale-110 transition-transform" />
              </button>
            </div>

            {/* Zoom Level Indicator */}
            <div className="absolute top-6 right-6 bg-background/90 border border-border px-4 py-2 backdrop-blur-sm z-30">
              <span className="text-[9px] font-bold uppercase tracking-widest opacity-40">
                Interactive Mode
              </span>
            </div>

            <TransformComponent 
              wrapperClassName="!w-full !h-full !cursor-grab active:!cursor-grabbing" 
              contentClassName="!w-full !h-full flex items-center justify-center"
            >
              {!diagram ? (
                <div className="flex flex-col items-center gap-4 opacity-10">
                  <div className="flex gap-2">
                    {[...Array(3)].map((_, i) => <div key={i} className="w-1.5 h-1.5 bg-foreground" />)}
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-[0.4em]">Initialize_Canvas</span>
                </div>
              ) : (
                <div 
                  ref={containerRef} 
                  className="mermaid-container p-12"
                  style={{
                    minWidth: '800px',
                    minHeight: '600px',
                  }}
                />
              )}
            </TransformComponent>
          </>
        )}
      </TransformWrapper>

      {/* VIEWPORT CORNERS */}
      <div className="absolute top-0 left-0 w-10 h-10 border-t-2 border-l-2 border-accent/20 pointer-events-none" />
      <div className="absolute top-0 right-0 w-10 h-10 border-t-2 border-r-2 border-accent/20 pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-10 h-10 border-b-2 border-l-2 border-accent/20 pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-10 h-10 border-b-2 border-r-2 border-accent/20 pointer-events-none" />
    </div>
  );
}