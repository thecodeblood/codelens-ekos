import React from 'react';
import { FileText, MapPin } from 'lucide-react';

const CitationsList = ({ citations }) => {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="glass-panel animate-fade-in" style={{ padding: '24px' }}>
      <h3 style={{ marginBottom: '16px', color: 'var(--text-secondary)' }}>Evidence & Citations</h3>
      <div style={{ display: 'grid', gap: '12px', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))' }}>
        {citations.map((cite, idx) => (
          <div key={idx} style={{ 
            background: 'rgba(255,255,255,0.03)', 
            border: '1px solid var(--border-glass)', 
            padding: '12px', 
            borderRadius: '8px',
            fontSize: '0.85rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ 
                background: 'var(--accent-glow)', 
                color: 'var(--accent-purple)', 
                padding: '2px 8px', 
                borderRadius: '12px',
                fontWeight: 'bold'
              }}>
                [{idx + 1}]
              </span>
              <strong style={{ color: 'var(--text-primary)' }}>{cite.name}</strong>
              <span style={{ color: 'var(--text-secondary)' }}>({cite.type})</span>
            </div>
            
            {cite.source_uri && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                <FileText size={14} />
                <span style={{ wordBreak: 'break-all' }}>{cite.source_uri}</span>
              </div>
            )}
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)' }}>
              <MapPin size={14} />
              <span>Extracted via {cite.extraction_method} (Confidence: {cite.confidence})</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CitationsList;
