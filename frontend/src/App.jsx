import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import SearchBox from './components/SearchBox';
import DiagramViewer from './components/DiagramViewer';
import CitationsList from './components/CitationsList';
import Dashboard from './components/Dashboard';
import { executeQuery } from './api';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSearch = async (query) => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await executeQuery(query);
      setResult(data);
    } catch (err) {
      setError(err.message || 'An error occurred while fetching the response.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '40px 20px' }}>
      <header style={{ textAlign: 'center', marginBottom: '40px' }}>
        <h1 style={{ 
          fontSize: '3rem', 
          background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-purple))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          marginBottom: '8px'
        }}>
          CodeLens EKOS
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>
          Ask architectural questions about your software system
        </p>
      </header>

      {!result && !isLoading && <Dashboard />}

      <SearchBox onSearch={handleSearch} isLoading={isLoading} />

      {error && (
        <div className="glass-panel animate-fade-in" style={{ padding: '16px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--error)', color: 'var(--error)' }}>
          {error}
        </div>
      )}

      {result && (
        <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="glass-panel" style={{ padding: '32px' }}>
            <h3 style={{ marginBottom: '16px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px', fontSize: '0.8rem' }}>
              Intent: {result.intent}
            </h3>
            <div className="markdown-body">
              <ReactMarkdown>{result.markdown}</ReactMarkdown>
            </div>
          </div>
          
          <DiagramViewer diagramDefinition={result.diagram} />
          
          <CitationsList citations={result.citations} />
        </div>
      )}
    </div>
  );
}

export default App;
