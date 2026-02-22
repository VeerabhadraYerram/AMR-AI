import React from 'react';
import { ArrowUp, ArrowDown, HelpCircle, Minus } from 'lucide-react';

const GeneDrivers = ({ data }) => {
    return (
        <section className="card">
            <div className="flex-row" style={{ justifyContent: 'space-between' }}>
                <h2 className="section-title">Gene Drivers (Mechanism View)</h2>
                <HelpCircle size={18} color="var(--color-text-secondary)" />
            </div>

            <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead>
                        <tr style={{ borderBottom: '2px solid var(--color-border)', color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>
                            <th style={{ padding: 'var(--spacing-sm)' }}>Gene/Mechanism</th>
                            <th style={{ padding: 'var(--spacing-sm)' }}>Contribution</th>
                            <th style={{ padding: 'var(--spacing-sm)' }}>Direction</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.genes.length === 0 ? (
                            <tr>
                                <td colSpan="3" style={{ padding: '1rem', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
                                    No significant gene drivers detected for this sample.
                                </td>
                            </tr>
                        ) : (
                            data.genes.map((gene, index) => (
                                <tr key={index} style={{ borderBottom: index < data.genes.length - 1 ? '1px solid var(--color-border)' : 'none' }}>
                                    <td style={{ padding: 'var(--spacing-md) var(--spacing-sm)', fontWeight: 500, fontFamily: 'monospace', fontSize: '1rem' }}>
                                        {gene.name}
                                    </td>
                                    <td style={{ padding: 'var(--spacing-md) var(--spacing-sm)' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <div style={{
                                                width: '100px',
                                                height: '8px',
                                                backgroundColor: '#e9ecef',
                                                borderRadius: '4px',
                                                overflow: 'hidden'
                                            }}>
                                                <div style={{
                                                    width: `${Math.min(gene.score * 100, 100)}%`,
                                                    height: '100%',
                                                    backgroundColor: 'var(--color-primary)'
                                                }} />
                                            </div>
                                            <span style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
                                                {gene.score.toFixed(4)}
                                            </span>
                                        </div>
                                    </td>
                                    <td style={{ padding: 'var(--spacing-md) var(--spacing-sm)' }}>
                                        <div className="flex-row" style={{ gap: '4px', color: gene.direction === 'increase' ? 'var(--color-danger)' : 'var(--color-success)' }}>
                                            {gene.direction === 'increase' ? (
                                                <>
                                                    <ArrowUp size={16} />
                                                    <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>Resistant</span>
                                                </>
                                            ) : (
                                                <>
                                                    <ArrowDown size={16} />
                                                    <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>Susceptible</span>
                                                </>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </section>
    );
};

export default GeneDrivers;
