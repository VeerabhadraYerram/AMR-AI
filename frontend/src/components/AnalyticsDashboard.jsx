import React, { useState, useEffect } from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
    PieChart, Pie, Cell, BarChart, Bar
} from 'recharts';
import { getTrendsData, getHeatmapData, getAntibiotics, getMapData } from '../services/api';
import { Filter, Calendar, Activity, Map as MapIcon, Grid } from 'lucide-react';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658'];

// Simple Heatmap Component
const Heatmap = ({ data, xLabels, yLabels }) => {
    if (!data || data.length === 0) return <div className="no-data">No Heatmap Data</div>;

    // Normalize value for color intensity (0-100)
    const getColor = (value) => {
        if (value === -1) return '#f5f5f5'; // No data
        // Green (low) -> Yellow -> Red (high)
        const intensity = value / 100;
        if (intensity < 0.5) {
            // green to yellow
            const g = 255;
            const r = Math.round(510 * intensity);
            return `rgba(${r}, ${g}, 0, 0.7)`;
        } else {
            // yellow to red
            const r = 255;
            const g = Math.round(510 * (1 - intensity));
            return `rgba(${r}, ${g}, 0, 0.7)`;
        }
    };

    return (
        <div style={{ overflowX: 'auto', maxWidth: '100%' }}>
            <table style={{ borderCollapse: 'collapse', fontSize: '0.8rem', width: '100%' }}>
                <thead>
                    <tr>
                        <th style={{ padding: '8px', textAlign: 'left', minWidth: '120px' }}>Antibiotic / Pathogen</th>
                        {xLabels.map(label => (
                            <th key={label} style={{ padding: '8px', textAlign: 'center', borderBottom: '1px solid #ddd' }}>{label}</th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {yLabels.map((yLabel, yIndex) => (
                        <tr key={yLabel}>
                            <td style={{ padding: '8px', fontWeight: 500, borderRight: '1px solid #ddd' }}>{yLabel}</td>
                            {data[yIndex].map((rawVal, xIndex) => {
                                const value = rawVal === -1 ? -1 : rawVal * 100;
                                return (
                                    <td key={`${yIndex}-${xIndex}`} style={{
                                        backgroundColor: getColor(value),
                                        color: value > 50 ? 'white' : 'black',
                                        textAlign: 'center',
                                        padding: '8px',
                                        border: '1px solid #eee'
                                    }}
                                        title={`${yLabel} vs ${xLabels[xIndex]}: ${value === -1 ? 'No Data' : value.toFixed(1) + '%'}`}
                                    >
                                        {value === -1 ? '-' : `${Math.round(value)}%`}
                                    </td>
                                );
                            })}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

const AnalyticsDashboard = () => {
    const [trendsData, setTrendsData] = useState(null);
    const [heatmapData, setHeatmapData] = useState(null);
    const [regionalData, setRegionalData] = useState(null);
    const [antibiotics, setAntibiotics] = useState([]);

    // Filters
    const [selectedAntibiotic, setSelectedAntibiotic] = useState('');
    const [selectedPathogen, setSelectedPathogen] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadInitialData();
    }, []);

    useEffect(() => {
        loadTrends();
        loadRegionalComparison();
    }, [selectedAntibiotic, selectedPathogen]);

    const loadInitialData = async () => {
        setLoading(true);
        try {
            const [abList, hData] = await Promise.all([
                getAntibiotics(),
                getHeatmapData()
            ]);
            setAntibiotics(abList);
            setHeatmapData(hData);
            await loadTrends(); // Load initial trends
            await loadRegionalComparison();
        } catch (e) {
            console.error("Dashboard init error", e);
        }
        setLoading(false);
    };

    const loadTrends = async () => {
        try {
            const filters = {};
            if (selectedAntibiotic) filters.antibiotic = selectedAntibiotic;
            if (selectedPathogen) filters.pathogen = selectedPathogen;

            const res = await getTrendsData(filters);
            if (res && res.labels) {
                const formatted = res.labels.map((year, i) => ({
                    year,
                    value: res.datasets[0].data[i] * 100 // Convert to percentage
                }));
                const pathogenDist = res.pathogen_distribution || [];
                setTrendsData({ trends: formatted, pathogens: pathogenDist });
            }
        } catch (e) {
            console.error("Trend load error", e);
        }
    };

    const loadRegionalComparison = async () => {
        try {
            // Use 'antibiotic_performance' endpoint to get regional distribution
            // passing selectedAntibiotic to filter
            const res = await getMapData('antibiotic_performance', selectedAntibiotic);
            if (res && res.data) {
                // Filter out 'interpolated' or 'Other' if desired, or keep all
                // Sort by resistance value descending
                const sorted = [...res.data]
                    .filter(d => d.value > 0)
                    .sort((a, b) => b.value - a.value)
                    .slice(0, 10); // Top 10 regions

                setRegionalData(sorted);
            }
        } catch (e) {
            console.error("Regional load error", e);
        }
    };

    if (loading) return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-text-secondary)' }}>Loading Analytics Dashboard...</div>;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-lg)' }}>

            {/* Header & Controls */}
            <section className="card">
                <div className="flex-row" style={{ justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <div>
                        <h2 className="section-title">Surveillance Analytics</h2>
                        <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>
                            Comprehensive policy-relevant insights from integrated surveillance data.
                        </p>
                    </div>
                    <div className="flex-row" style={{ gap: '10px', alignItems: 'center' }}>
                        <Filter size={18} color="var(--color-text-secondary)" />

                        {/* Antibiotic Filter */}
                        <select
                            value={selectedAntibiotic}
                            onChange={(e) => setSelectedAntibiotic(e.target.value)}
                            style={{
                                padding: '8px',
                                borderRadius: '4px',
                                border: '1px solid var(--color-border)',
                                minWidth: '200px'
                            }}
                        >
                            <option value="">All Antibiotics (Aggregate)</option>
                            {antibiotics.map(ab => (
                                <option key={ab} value={ab}>{ab}</option>
                            ))}
                        </select>

                        {/* Pathogen Filter */}
                        <select
                            value={selectedPathogen}
                            onChange={(e) => setSelectedPathogen(e.target.value)}
                            style={{
                                padding: '8px',
                                borderRadius: '4px',
                                border: '1px solid var(--color-border)',
                                minWidth: '180px'
                            }}
                        >
                            <option value="">All Pathogens</option>
                            {["E. coli", "K. pneumoniae", "S. aureus", "Acinetobacter", "Pseudomonas"].map(p => (
                                <option key={p} value={p}>{p}</option>
                            ))}
                        </select>
                    </div>
                </div>
            </section>

            <div className="grid-2">
                {/* 1. Resistance Trends */}
                <section className="card" style={{ minHeight: '350px' }}>
                    <div className="card-header" style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Activity size={18} color="var(--color-primary)" />
                        <h3 style={{ fontSize: '1rem', margin: 0 }}>
                            {selectedAntibiotic ? `${selectedAntibiotic} ` : 'Aggregate '}
                            Resistance Trends
                            {selectedPathogen ? ` (${selectedPathogen})` : ''}
                        </h3>
                    </div>
                    {trendsData?.trends && (
                        <ResponsiveContainer width="100%" height={280}>
                            <LineChart data={trendsData.trends}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                <XAxis dataKey="year" />
                                <YAxis domain={[0, 100]} label={{ value: 'Resistance %', angle: -90, position: 'insideLeft' }} />
                                <Tooltip formatter={(val) => `${val.toFixed(1)}%`} itemStyle={{ color: '#8884d8' }} />
                                <Legend />
                                <Line
                                    type="monotone"
                                    dataKey="value"
                                    name="Resistance Rate"
                                    stroke="#8884d8"
                                    strokeWidth={3}
                                    activeDot={{ r: 8 }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    )}
                </section>

                {/* 2. Regional Comparison (Bar Chart) */}
                <section className="card" style={{ minHeight: '350px' }}>
                    <div className="card-header" style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <MapIcon size={18} color="var(--color-primary)" />
                        <h3 style={{ fontSize: '1rem', margin: 0 }}>
                            Top 10 High-Resistance States {selectedAntibiotic && `(${selectedAntibiotic})`}
                        </h3>
                    </div>
                    {regionalData && regionalData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={280}>
                            <BarChart data={regionalData} layout="vertical" margin={{ left: 40 }}>
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                                <XAxis type="number" domain={[0, 100]} />
                                <YAxis dataKey="region" type="category" width={100} style={{ fontSize: '0.8rem' }} />
                                <Tooltip
                                    formatter={(val) => `${val}%`}
                                    content={({ active, payload }) => {
                                        if (active && payload && payload.length) {
                                            const data = payload[0].payload;
                                            return (
                                                <div style={{ backgroundColor: 'white', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}>
                                                    <p style={{ fontWeight: 'bold', margin: '0 0 4px 0' }}>{data.region}</p>
                                                    <p style={{ margin: 0, color: '#f44336' }}>R: {data.value}% (n={data.metadata.isolates})</p>
                                                    {data.metadata.estimated && <p style={{ fontSize: '0.8rem', color: '#999', margin: 0 }}>(Estimated)</p>}
                                                </div>
                                            );
                                        }
                                        return null;
                                    }}
                                />
                                <Bar dataKey="value" fill="#f44336" radius={[0, 4, 4, 0]} name="Resistance %" />
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--color-text-secondary)' }}>
                            No regional data available
                        </div>
                    )}
                </section>
            </div>

            {/* 3. Heatmap Matrix */}
            <section className="card">
                <div className="card-header" style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Grid size={18} color="var(--color-primary)" />
                    <h3 style={{ fontSize: '1rem', margin: 0 }}>Antibiotic vs. Pathogen Resistance Matrix</h3>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: '1rem' }}>
                    Heatmap showing resistance rates (Red = High, Green = Low). Grey indicates insufficient data.
                    Use this to identify which antibiotics are still effective against specific pathogens.
                </p>
                {heatmapData && (
                    <Heatmap
                        data={heatmapData.data}
                        xLabels={heatmapData.x_labels}
                        yLabels={heatmapData.y_labels}
                    />
                )}
            </section>

            {/* 4. Pathogen Distribution */}
            <div className="grid-2">
                <section className="card" style={{ minHeight: '300px' }}>
                    <div className="card-header" style={{ marginBottom: '1rem' }}>
                        <h3 style={{ fontSize: '1rem', margin: 0 }}>Pathogen Distribution</h3>
                    </div>
                    {trendsData?.pathogens && trendsData.pathogens.length > 0 ? (
                        <ResponsiveContainer width="100%" height={250}>
                            <PieChart>
                                <Pie
                                    data={trendsData.pathogens}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={50}
                                    outerRadius={80}
                                    fill="#8884d8"
                                    paddingAngle={5}
                                    dataKey="value"
                                >
                                    {trendsData.pathogens.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip />
                                <Legend layout="vertical" align="right" verticalAlign="middle" />
                            </PieChart>
                        </ResponsiveContainer>
                    ) : (
                        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>No pathogen data</div>
                    )}
                </section>

                {/* 5. Key Insights Panel */}
                <section className="card" style={{ backgroundColor: 'var(--color-surface-variant)' }}>
                    <div className="card-header" style={{ marginBottom: '1rem' }}>
                        <h3 style={{ fontSize: '1rem', margin: 0 }}>Policy Insights</h3>
                    </div>
                    <ul style={{ paddingLeft: '20px', fontSize: '0.9rem', color: 'var(--color-text-primary)' }}>
                        <li style={{ marginBottom: '8px' }}>
                            <strong>Carbapenem Resistance:</strong> High resistance in Klebsiella and E. coli indicates urgent need for stewardship in ICUs.
                        </li>
                        <li style={{ marginBottom: '8px' }}>
                            <strong>Regional Variation:</strong> Significant disparities between North and South India suggest local transmission dynamics.
                        </li>
                        <li style={{ marginBottom: '8px' }}>
                            <strong>Recommendation:</strong> Prioritize access to reserve antibiotics (e.g., Colistin) in high-burden red zones shown in the map.
                        </li>
                    </ul>
                </section>
            </div>
        </div>
    );
};

export default AnalyticsDashboard;
