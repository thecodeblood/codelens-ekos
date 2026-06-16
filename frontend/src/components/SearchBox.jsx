import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';

const SearchBox = ({ onSearch, isLoading }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query.trim());
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
      <h2 style={{ marginBottom: '16px', fontSize: '1.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Search size={24} color="var(--accent-blue)" />
        Ask CodeLens
      </h2>
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '12px' }}>
        <input
          type="text"
          className="input-glass"
          placeholder="e.g. How does Authentication work? or What depends on Booking?"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={isLoading}
        />
        <button type="submit" className="btn-primary" disabled={isLoading || !query.trim()}>
          {isLoading ? <Loader2 className="animate-spin" /> : 'Analyze'}
        </button>
      </form>
    </div>
  );
};

export default SearchBox;
