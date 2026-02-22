import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const CrossPathogenComparison = ({ data }) => {
    const chartData = data.pathogens.map(p => ({
        name: p.name,
        risk: p.risk * 100,
        count: p.count
    }));

    return (
        <section className="card">
            <h2 className="section-title">Cross-Pathogen Comparison</h2>

            <div className="grid-2">
                {/* Cards */}
                <div className="flex-col">
                    {data.pathogens.map(p => (
                        <div key={p.name} style={{
                            padding: 'var(--spacing-md)',
                            border: '1px solid var(--color-border)',
                            borderRadius: 'var(--radius-md)',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center'
                        }}>
                            <div>
                                <h4 style={{ margin: 0, color: 'var(--color-primary)' }}>{p.name}</h4>
                                <span style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>N = {p.count} isolates</span>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: p.risk > 0.5 ? 'var(--color-danger)' : 'var(--color-success)' }}>
                                    {(p.risk * 100).toFixed(1)}%
                                </div>
                                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>Resistance Rate</div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Chart */}
                <div style={{ height: '200px' }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                            <XAxis type="number" domain={[0, 100]} hide />
                            <YAxis dataKey="name" type="category" width={100} tick={{ fill: 'var(--color-text-primary)' }} />
                            <Tooltip
                                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: 'var(--shadow-md)' }}
                                formatter={(value) => [`${value}%`, 'Risk']}
                            />
                            <Bar dataKey="risk" radius={[0, 4, 4, 0]} barSize={20}>
                                {chartData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.risk > 50 ? 'var(--color-danger)' : 'var(--color-success)'} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </section>
    );
};

export default CrossPathogenComparison;
