import React, { useState, useEffect } from 'react';
import { Database, Plus, Upload, Link as LinkIcon, RefreshCw, Github } from 'lucide-react';
import { getSources, addSource, uploadDocument, triggerIngestion } from '../api';

const SourcesManager = () => {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sourceType, setSourceType] = useState('github');
  const [uri, setUri] = useState('');
  const [file, setFile] = useState(null);

  const loadSources = async () => {
    try {
      const data = await getSources();
      setSources(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadSources();
  }, []);

  const handleAddSource = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (sourceType === 'pdf' && file) {
        await uploadDocument(file);
      } else {
        await addSource(sourceType, uri);
      }
      setUri('');
      setFile(null);
      await loadSources();
    } catch (e) {
      console.error(e);
      alert("Failed to add source");
    } finally {
      setLoading(false);
    }
  };

  const handleIngest = async (sourceId) => {
    try {
      alert("Ingestion started. This might take a minute.");
      await triggerIngestion(sourceId);
      await loadSources();
      alert("Ingestion complete!");
    } catch (e) {
      console.error(e);
      alert("Ingestion failed!");
    }
  };

  return (
    <div className="glass-panel animate-fade-in" style={{ padding: '24px', marginBottom: '24px' }}>
      <h3 style={{ marginBottom: '20px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Database size={20} color="var(--accent-blue)" />
        Knowledge Sources
      </h3>

      <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
        <form onSubmit={handleAddSource} style={{ flex: '1', minWidth: '300px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <select 
            value={sourceType} 
            onChange={(e) => setSourceType(e.target.value)}
            style={{ padding: '12px', borderRadius: '8px', border: '1px solid var(--border-glass)', background: 'rgba(0,0,0,0.2)', color: 'white' }}
          >
            <option value="github">GitHub Repository URL</option>
            <option value="web">Web/Confluence URL</option>
            <option value="pdf">Upload PDF Document</option>
            <option value="local">Local Directory Path</option>
          </select>

          {sourceType === 'pdf' ? (
            <input 
              type="file" 
              accept=".pdf"
              onChange={(e) => setFile(e.target.files[0])}
              style={{ padding: '12px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', color: 'white' }}
              required
            />
          ) : (
            <input 
              type="text" 
              placeholder="Enter URL or Path..." 
              value={uri}
              onChange={(e) => setUri(e.target.value)}
              style={{ padding: '12px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', color: 'white', border: '1px solid var(--border-glass)' }}
              required
            />
          )}

          <button 
            type="submit" 
            disabled={loading}
            style={{ padding: '12px', background: 'var(--accent-blue)', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
          >
            {sourceType === 'pdf' ? <Upload size={18} /> : <Plus size={18} />}
            {loading ? 'Adding...' : 'Attach Source'}
          </button>
        </form>

        <div style={{ flex: '2', minWidth: '300px', background: 'rgba(0,0,0,0.1)', borderRadius: '8px', padding: '16px', maxHeight: '250px', overflowY: 'auto' }}>
          {sources.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)' }}>No sources attached yet.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {sources.map(source => (
                <div key={source.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '8px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 'bold' }}>
                      {source.type === 'github' ? <Github size={16} /> : <LinkIcon size={16} />}
                      {source.name}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                      {source.status === 'ingested' ? '✅ Ingested' : source.status === 'error' ? '❌ Error' : '⏳ Pending'}
                    </div>
                  </div>
                  <button 
                    onClick={() => handleIngest(source.id)}
                    style={{ background: 'transparent', border: '1px solid var(--border-glass)', color: 'white', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
                  >
                    <RefreshCw size={14} /> Ingest
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SourcesManager;
