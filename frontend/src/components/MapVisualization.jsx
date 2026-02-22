import React, { useState, useEffect } from 'react';
import { getMapData, getAntibiotics } from '../services/api';
import { Map, AlertCircle, Filter } from 'lucide-react';
import IndiaMap from './IndiaMap';

const MapVisualization = () => {
    const [mapType, setMapType] = useState('antibiotic_performance');
    const [mapData, setMapData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [antibiotics, setAntibiotics] = useState([]);
    const [selectedAntibiotic, setSelectedAntibiotic] = useState('');

    useEffect(() => {
        // Load antibiotic list on mount
        const loadAntibiotics = async () => {
            const list = await getAntibiotics();
            setAntibiotics(list);
        };
        loadAntibiotics();
    }, []);

    useEffect(() => {
        fetchMapData(mapType, selectedAntibiotic);
    }, [mapType, selectedAntibiotic]);

    const fetchMapData = async (type, antibiotic) => {
        setLoading(true);
        try {
            // clear antibiotic selection if switching to carbapenem view (it's a fixed view)
            if (type === 'carbapenem_resistance' && antibiotic) {
                setSelectedAntibiotic('');
                antibiotic = null;
            }

            const data = await getMapData(type, antibiotic);
            setMapData(data);
        } catch (error) {
            console.error("Failed to fetch map data", error);
        }
        setLoading(false);
    };

    const handleAntibioticChange = (e) => {
        setSelectedAntibiotic(e.target.value);
        // Force switch to 'antibiotic_performance' if selecting a drug
        if (mapType !== 'antibiotic_performance') {
            setMapType('antibiotic_performance');
        }
    };

    return (
        <section className="card">
            <div className="flex-row" style={{ justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--spacing-md)', flexWrap: 'wrap', gap: '1rem' }}>
                <div style={{ flex: 1, minWidth: '300px' }}>
                    <h2 className="section-title" style={{ marginBottom: '4px' }}>India Regional Surveillance</h2>
                    <p style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)', margin: 0 }}>
                        {mapType === 'antibiotic_performance' ? (
                            selectedAntibiotic
                                ? `Resistance rates for ${selectedAntibiotic} across Indian states.`
                                : 'Overall antibiotic resistance rates across Indian states.'
                        ) : (
                            'Carbapenem (last-resort antibiotic) resistance — high rates signal critical AMR threat zones.'
                        )}
                    </p>
                </div>

                <div className="flex-row" style={{ gap: '12px', flexShrink: 0, alignItems: 'center' }}>
                    {/* Antibiotic Selector */}
                    <div style={{ position: 'relative' }}>
                        <Filter size={16} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-secondary)' }} />
                        <select
                            value={selectedAntibiotic}
                            onChange={handleAntibioticChange}
                            style={{
                                padding: '6px 12px 6px 32px',
                                borderRadius: '4px',
                                border: '1px solid var(--color-border)',
                                backgroundColor: 'var(--color-background)',
                                fontSize: '0.9rem',
                                maxWidth: '200px'
                            }}
                        >
                            <option value="">All Antibiotics</option>
                            {antibiotics.map(ab => (
                                <option key={ab} value={ab}>{ab}</option>
                            ))}
                        </select>
                    </div>

                    <div className="flex-row" style={{ gap: '4px' }}>
                        <button
                            onClick={() => { setMapType('antibiotic_performance'); setSelectedAntibiotic(''); }}
                            style={{
                                padding: '6px 12px',
                                cursor: 'pointer',
                                backgroundColor: (mapType === 'antibiotic_performance' && !selectedAntibiotic) ? 'var(--color-primary)' : 'var(--color-background)',
                                color: (mapType === 'antibiotic_performance' && !selectedAntibiotic) ? 'white' : 'var(--color-text-primary)',
                                border: '1px solid var(--color-border)',
                                borderRadius: '4px',
                                fontWeight: 500
                            }}
                        >
                            Overall
                        </button>
                        <button
                            onClick={() => setMapType('carbapenem_resistance')}
                            style={{
                                padding: '6px 12px',
                                cursor: 'pointer',
                                backgroundColor: mapType === 'carbapenem_resistance' ? 'var(--color-primary)' : 'var(--color-background)',
                                color: mapType === 'carbapenem_resistance' ? 'white' : 'var(--color-text-primary)',
                                border: '1px solid var(--color-border)',
                                borderRadius: '4px',
                                fontWeight: 500
                            }}
                        >
                            Carbapenem
                        </button>
                    </div>
                </div>
            </div>

            <div style={{
                minHeight: '400px',
                backgroundColor: 'var(--color-surface)',
                borderRadius: 'var(--radius-md)',
                padding: '20px',
                border: '1px solid var(--color-border)',
                position: 'relative'
            }}>
                {loading ? (
                    <div style={{ textAlign: 'center', padding: '100px', color: 'var(--color-text-secondary)' }}>Loading Surveillance Data...</div>
                ) : (
                    <>
                        {(!mapData || mapData.status === 'unavailable') ? (
                            <div style={{ textAlign: 'center', color: 'var(--color-text-secondary)', padding: '40px' }}>
                                <Map size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', color: 'var(--color-warning)', marginBottom: '8px' }}>
                                    <AlertCircle size={20} />
                                    <span style={{ fontWeight: 600 }}>Data Unavailable</span>
                                </div>
                                <p>{mapData?.message || "Regional metadata missing."}</p>
                            </div>
                        ) : (
                            <IndiaMap data={mapData} mapType={mapType} />
                        )}
                    </>
                )}
            </div>
        </section>
    );
};

export default MapVisualization;
