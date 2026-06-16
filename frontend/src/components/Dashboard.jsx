import React, { useEffect, useState } from 'react';
import { getModelQuality } from '../api';
import { Activity, Database, CheckCircle, AlertTriangle } from 'lucide-react';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getModelQuality();
        setStats(data);
      } catch (err) {
        console.error("Failed to load dashboard stats", err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading || !stats) return null;

  return (
    <div className="glass-panel animate-fade-in" style={{ padding: '24px', marginBottom: '24px' }}>
      <h3 style={{ marginBottom: '20px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Activity size={20} color="var(--success)" />
        System Model Health
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        
        <div style={{ background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '8px' }}>Integrity Score</div>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: stats.score > 80 ? 'var(--success)' : 'var(--warning)' }}>
            {stats.score}%
          </div>
        </div>

        <div style={{ background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '8px' }}>Total Nodes</div>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Database size={24} color="var(--accent-blue)" />
            {stats.stats?.nodes_count || 0}
          </div>
        </div>

        <div style={{ background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '8px' }}>Total Edges</div>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>
            {stats.stats?.edges_count || 0}
          </div>
        </div>

        <div style={{ background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '8px' }}>Issues Detected</div>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: stats.errors?.length > 0 ? 'var(--error)' : 'var(--success)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            {stats.errors?.length > 0 ? <AlertTriangle size={24} /> : <CheckCircle size={24} />}
            {stats.errors?.length || 0}
          </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
