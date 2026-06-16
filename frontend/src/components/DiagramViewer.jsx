import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'loose',
  fontFamily: 'Inter, sans-serif',
});

const DiagramViewer = ({ diagramDefinition }) => {
  const containerRef = useRef(null);

  useEffect(() => {
    if (diagramDefinition && containerRef.current) {
      // Clear previous diagram
      containerRef.current.innerHTML = '';
      
      try {
        mermaid.render('mermaid-graph', diagramDefinition).then((result) => {
          containerRef.current.innerHTML = result.svg;
        });
      } catch (e) {
        console.error('Mermaid render error', e);
        containerRef.current.innerHTML = `<div style="color: var(--error)">Failed to render diagram: ${e.message}</div>`;
      }
    }
  }, [diagramDefinition]);

  if (!diagramDefinition) return null;

  return (
    <div className="glass-panel animate-fade-in" style={{ padding: '24px', marginBottom: '24px', overflowX: 'auto' }}>
      <h3 style={{ marginBottom: '16px', color: 'var(--text-secondary)' }}>System Graph</h3>
      <div 
        ref={containerRef} 
        style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          background: 'rgba(0,0,0,0.2)', 
          borderRadius: '8px',
          padding: '16px' 
        }} 
      />
    </div>
  );
};

export default DiagramViewer;
