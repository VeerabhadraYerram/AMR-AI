import React from 'react';
import { Activity } from 'lucide-react';

const Header = () => {
  return (
    <header style={{
      backgroundColor: 'var(--color-surface)',
      borderBottom: '1px solid var(--color-border)',
      padding: 'var(--spacing-md) 0',
      marginBottom: 'var(--spacing-lg)'
    }}>
      <div className="container flex-row" style={{ justifyContent: 'space-between' }}>
        <div className="flex-col" style={{ gap: 'var(--spacing-xs)' }}>
          <h1 style={{ margin: 0, fontSize: '1.5rem', color: 'var(--color-primary)' }}>
            Antibiotic Resistance Intelligence Dashboard
          </h1>
          <p style={{ margin: 0, color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>
            Gene-Attributable Cross-Pathogen Analysis
          </p>
        </div>
        
        <div className="flex-row" style={{ color: 'var(--color-secondary)' }}>
          <Activity size={24} />
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>AMR-AI Platform</span>
        </div>
      </div>
    </header>
  );
};

export default Header;
