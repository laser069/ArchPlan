'use client';
import { useEffect, useRef } from 'react';
import mermaid from 'mermaid';
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import { ZoomIn, ZoomOut, Maximize } from 'lucide-react';

const DEFAULT_DIAGRAM = `
graph LR
    subgraph Client_Layer
        User[User Interface]
        CDN[Edge Network]
    end

    subgraph Logic_Layer
        LB[Load Balancer]
        API[API Gateway]
        SVC[Core Services]
    end

    subgraph Data_Layer
        DB[(Primary Database)]
        Cache(Shared Cache)
    end

    User --> CDN
    CDN --> LB
    LB --> API
    API --> SVC
    SVC --> DB
    SVC --> Cache
`;

// Injected into the SVG after render for reliable, cascade-proof styling
const SVG_STYLE = `
  .node rect, .node circle, .node ellipse, .node polygon, .node path {
    stroke-width: 2px !important;
  }
  .node .label, .nodeLabel, .edgeLabel, .cluster-label {
    font-family: 'Inter', system-ui, sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    fill: #0f172a !important;
    color: #0f172a !important;
  }
  .edgeLabel {
    font-size: 12px !important;
    font-weight: 500 !important;
    background: #f8fafc !important;
    padding: 2px 4px !important;
    border-radius: 3px !important;
  }
  .edgePath path {
    stroke-width: 2px !important;
    stroke: #475569 !important;
  }
  .arrowheadPath {
    fill: #475569 !important;
  }
  .cluster rect {
    stroke-width: 1.5px !important;
    rx: 8px !important;
  }
  /* Subgraph label */
  .cluster span, .cluster .nodeLabel {
    font-size: 13px !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
  }
`;

export default function Canvas({ diagram }: { diagram: string | null }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'base',
      themeVariables: {
        fontFamily: "'Inter', system-ui, sans-serif",
        fontSize: '14px',
        // Node fill/stroke
        primaryColor: '#f0f9ff',
        primaryTextColor: '#0f172a',
        primaryBorderColor: '#0ea5e9',
        // Secondary (e.g. subgraph fill)
        secondaryColor: '#f8fafc',
        secondaryTextColor: '#0f172a',
        secondaryBorderColor: '#cbd5e1',
        // Tertiary
        tertiaryColor: '#fefce8',
        tertiaryTextColor: '#0f172a',
        tertiaryBorderColor: '#fbbf24',
        // Edges & background
        lineColor: '#475569',
        edgeLabelBackground: '#f8fafc',
        mainBkg: '#ffffff',
        nodeBorder: '#0ea5e9',
        clusterBkg: '#f8fafc',
        clusterBorder: '#cbd5e1',
        titleColor: '#0f172a',
      },
      flowchart: {
        curve: 'basis',
        padding: 40,
        htmlLabels: true,
        nodeSpacing: 60,
        rankSpacing: 90,
        diagramPadding: 32,
        useMaxWidth: true,
      },
    });

    const renderDiagram = async () => {
      const content = diagram?.trim() || DEFAULT_DIAGRAM;
      const id = `mermaid-${Math.random().toString(36).slice(2, 9)}`;

      try {
        const clean = content.replace(/```mermaid/g, '').replace(/```/g, '').trim();
        const { svg } = await mermaid.render(id, clean);

        if (!containerRef.current) return;

        containerRef.current.innerHTML = svg;
        const svgEl = containerRef.current.querySelector('svg');
        if (!svgEl) return;

        // Let SVG fill container width, height auto
        svgEl.removeAttribute('height');
        svgEl.removeAttribute('width');
        svgEl.setAttribute('width', '100%');
        svgEl.style.width = '100%';
        svgEl.style.height = 'auto';
        svgEl.style.display = 'block';
        svgEl.style.overflow = 'visible';

        // Inject style tag inside SVG for reliable override
        const styleEl = document.createElementNS('http://www.w3.org/2000/svg', 'style');
        styleEl.textContent = SVG_STYLE;
        svgEl.prepend(styleEl);

        // Ensure foreignObject labels (htmlLabels) also inherit styling
        svgEl.querySelectorAll('foreignObject').forEach(fo => {
          const div = fo.querySelector('div');
          if (div) {
            div.style.fontSize = '14px';
            div.style.fontWeight = '600';
            div.style.color = '#0f172a';
            div.style.fontFamily = "'Inter', system-ui, sans-serif";
            div.style.lineHeight = '1.4';
          }
        });
      } catch (e) {
        console.error('Mermaid render error:', e);
        if (containerRef.current) {
          containerRef.current.innerHTML = `
            <div style="color:#ef4444;font-size:13px;font-family:monospace;padding:16px;">
              Diagram parse error. Check syntax.
            </div>`;
        }
      }
    };

    renderDiagram();
  }, [diagram]);

  return (
    <div className="relative w-full h-full bg-[#050505] overflow-hidden">
      <TransformWrapper
        initialScale={0.7}
        minScale={0.1}
        maxScale={4}
        centerOnInit
        limitToBounds={false}
        wheel={{ step: 0.08 }}
      >
        {({ zoomIn, zoomOut, resetTransform, centerView }) => (
          <>
            {/* Zoom controls */}
            <div className="absolute bottom-8 right-8 flex flex-col gap-1 z-30">
              {[
                { icon: <ZoomIn size={18} />, action: () => zoomIn(0.2), title: 'Zoom In' },
                { icon: <ZoomOut size={18} />, action: () => zoomOut(0.2), title: 'Zoom Out' },
                {
                  icon: <Maximize size={18} />,
                  action: () => { resetTransform(); centerView(0.7); },
                  title: 'Reset',
                },
              ].map(({ icon, action, title }) => (
                <button
                  key={title}
                  onClick={action}
                  title={title}
                  className="p-2.5 bg-white/90 backdrop-blur text-slate-800 hover:bg-cyan-500 hover:text-white transition-all border border-white/10 shadow-xl rounded"
                >
                  {icon}
                </button>
              ))}
            </div>

            <TransformComponent
              wrapperClassName="!w-full !h-full !cursor-grab active:!cursor-grabbing"
              contentClassName="!w-full !h-full flex items-center justify-center"
            >
              <div
                ref={containerRef}
                className={`
                  bg-white rounded-lg shadow-[0_0_80px_rgba(0,0,0,0.5)]
                  transition-all duration-700
                  ${!diagram ? 'opacity-25 scale-95 grayscale' : 'opacity-100 scale-100'}
                `}
                style={{
                  // Fluid: shrinks on small viewports, grows on large
                  width: 'clamp(640px, 80vw, 1400px)',
                  padding: '48px 56px',
                }}
              />
            </TransformComponent>
          </>
        )}
      </TransformWrapper>
    </div>
  );
}
