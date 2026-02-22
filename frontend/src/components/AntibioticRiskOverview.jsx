import React from 'react';
import { AlertTriangle, CheckCircle, AlertCircle, TrendingUp } from 'lucide-react';

const AntibioticRiskOverview = ({ selectedAntibiotic, onAntibioticChange, antibioticList, data }) => {
    const getRiskColor = (score) => {
        if (score < 0.33) return 'var(--color-success)';
        if (score < 0.66) return 'var(--color-warning)';
        return 'var(--color-danger)';
    };

    const riskColor = getRiskColor(data.overallRisk);

    return (
        <section className="card">
            <div className="flex-row" style={{ justifyContent: 'space-between', marginBottom: 'var(--spacing-lg)' }}>
                <h2 className="section-title" style={{ margin: 0 }}>Antibiotic-Level Risk Overview</h2>

                <select
                    value={selectedAntibiotic}
                    onChange={(e) => onAntibioticChange(e.target.value)}
                    style={{
                        padding: '8px 16px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--color-border)',
                        fontSize: '1rem',
                        color: 'var(--color-text-primary)',
                        backgroundColor: 'var(--color-background)',
                        cursor: 'pointer',
                        minWidth: '200px'
                    }}
                >
                    {antibioticList.map(ab => (
                        <option key={ab.id} value={ab.id}>{ab.name}</option>
                    ))}
                </select>
            </div>

            <div className="grid-2">
                {/* Risk Score Display */}
                <div style={{ padding: 'var(--spacing-md)', backgroundColor: 'var(--color-background)', borderRadius: 'var(--radius-md)' }}>
                    <div className="flex-row" style={{ alignItems: 'baseline', marginBottom: 'var(--spacing-sm)' }}>
                        <span style={{ fontSize: '3rem', fontWeight: 700, color: riskColor }}>
                            {(data.overallRisk * 100).toFixed(0)}%
                        </span>
                        <span style={{ fontSize: '1.2rem', fontWeight: 600, color: riskColor }}>
                            {data.riskLevel.toUpperCase()} RISK
                        </span>
                    </div>

                    <div style={{ marginBottom: 'var(--spacing-md)' }}>
                        <div style={{
                            height: '12px',
                            width: '100%',
                            backgroundColor: '#e9ecef',
                            borderRadius: '6px',
                            overflow: 'hidden'
                        }}>
                            <div style={{
                                height: '100%',
                                width: `${data.overallRisk * 100}%`,
                                backgroundColor: riskColor,
                                transition: 'width 0.5s ease-in-out'
                            }} />
                        </div>
                        <div className="flex-row" style={{ justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginTop: '4px' }}>
                            <span>Low Risk</span>
                            <span>Moderate</span>
                            <span>High Risk</span>
                        </div>
                    </div>
                </div>

                {/* Info & Confidence */}
                <div className="flex-col" style={{ justifyContent: 'center' }}>
                    <div className="flex-row" style={{ alignItems: 'center', color: 'var(--color-text-secondary)' }}>
                        <ActivityIcon score={data.overallRisk} />
                        <span style={{ marginLeft: '8px' }}>
                            Risk score indicates probability of resistance across monitored pathogens.
                        </span>
                    </div>

                    <div style={{ marginTop: 'var(--spacing-md)', padding: 'var(--spacing-sm)', borderLeft: '4px solid var(--color-secondary)', backgroundColor: '#f1fcfc' }}>
                        <div className="flex-row" style={{ justifyContent: 'space-between' }}>
                            <span style={{ fontWeight: 600, color: 'var(--color-primary)' }}>Model Confidence</span>
                            <span style={{ fontWeight: 700 }}>{(data.confidence * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};

const ActivityIcon = ({ score }) => {
    if (score < 0.33) return <CheckCircle size={24} color="var(--color-success)" />;
    if (score < 0.66) return <AlertCircle size={24} color="var(--color-warning)" />;
    return <AlertTriangle size={24} color="var(--color-danger)" />;
};

export default AntibioticRiskOverview;
