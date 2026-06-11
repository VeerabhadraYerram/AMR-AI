import React, { useMemo } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { scaleLinear } from "d3-scale";

// Leaflet uses [lat, lng]
const LOCALITIES_COORDS = {
    "Bachupally": [17.558, 78.384],
    "Nizampet": [17.518, 78.387],
    "Kukatpally": [17.484, 78.406],
    "Miyapur": [17.493, 78.361],
    "Gachibowli": [17.443, 78.346],
    "Kondapur": [17.462, 78.361],
    "Ameerpet": [17.437, 78.444],
    "Banjara Hills": [17.415, 78.414],
    "Secunderabad": [17.439, 78.502],
    "Uppal": [17.398, 78.560]
};

const COLOR_RANGES = {
    antibiotic_performance: {
        low: '#e8f5e9',
        high: '#b71c1c',
        label: 'Resistance Rate',
        stops: ['#e8f5e9', '#c8e6c9', '#ffecb3', '#ffcc02', '#ff9800', '#f44336', '#b71c1c']
    },
    carbapenem_resistance: {
        low: '#fff8e1',
        high: '#b71c1c',
        label: 'Carbapenem Resistance',
        stops: ['#fff8e1', '#ffe082', '#ffb74d', '#ff9800', '#f44336', '#d32f2f', '#b71c1c']
    }
};

const ActualHyderabadMap = ({ data, mapType }) => {
    // Build data map: locality name → { value, metadata }
    const dataMap = useMemo(() => {
        const map = {};
        if (data && data.data) {
            data.data.forEach(d => {
                map[d.region] = {
                    value: d.value,
                    metadata: d.metadata || {}
                };
            });
        }
        return map;
    }, [data]);

    const { minVal, maxVal } = useMemo(() => {
        let min = Infinity, max = -Infinity;
        if (data && data.data) {
            data.data.forEach(d => {
                if (d.value < min) min = d.value;
                if (d.value > max) max = d.value;
            });
        }
        if (min === Infinity) { min = 0; max = 100; }
        return { minVal: min, maxVal: max };
    }, [data]);

    const palette = COLOR_RANGES[mapType] || COLOR_RANGES.antibiotic_performance;

    const colorScale = useMemo(() => {
        return scaleLinear()
            .domain(palette.stops.map((_, i) => minVal + (maxVal - minVal) * (i / (palette.stops.length - 1))))
            .range(palette.stops)
            .clamp(true);
    }, [minVal, maxVal, palette]);

    // Calculate map center
    const center = [17.465, 78.43]; // Adjusted center of Hyderabad

    return (
        <div style={{ width: '100%', height: '500px', position: 'relative', borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--color-border)' }}>
            {/* Adding z-index 0 to MapContainer to fix dropdown menus hiding behind Leaflet pane */}
            <MapContainer center={center} zoom={11} style={{ width: '100%', height: '100%', zIndex: 0 }}>
                {/* Standard OpenStreetMap Tiles */}
                <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                />

                {Object.keys(LOCALITIES_COORDS).map(locality => {
                    const coords = LOCALITIES_COORDS[locality];
                    const info = dataMap[locality];

                    if (!info) return null;

                    const fillColor = colorScale(info.value);
                    const radius = Math.max(12, Math.min(30, info.value / 2)); // Dynamic radius based on resistance!

                    return (
                        <CircleMarker
                            key={locality}
                            center={coords}
                            pathOptions={{
                                fillColor: fillColor,
                                fillOpacity: 0.8,
                                color: '#333',
                                weight: 1.5
                            }}
                            radius={radius}
                        >
                            <Popup>
                                <div style={{ fontSize: '13px', minWidth: '150px' }}>
                                    <h4 style={{ margin: '0 0 5px 0', borderBottom: '1px solid #ccc', paddingBottom: '3px' }}>{locality}</h4>
                                    <p style={{ margin: '3px 0', fontWeight: 'bold' }}>Resistance: <span style={{ color: '#d32f2f' }}>{info.value}%</span></p>
                                    <p style={{ margin: '3px 0' }}>Isolates: {info.metadata.isolates}</p>
                                    {info.metadata.info && <p style={{ margin: '3px 0', fontSize: '11px', fontStyle: 'italic', color: '#666' }}>{info.metadata.info}</p>}
                                </div>
                            </Popup>
                        </CircleMarker>
                    );
                })}
            </MapContainer>

            {/* Gradient Legend Overlay */}
            <div style={{
                position: 'absolute',
                bottom: '20px',
                right: '20px',
                background: 'rgba(255,255,255,0.95)',
                padding: '10px 14px',
                borderRadius: '8px',
                fontSize: '0.8rem',
                boxShadow: '0 2px 10px rgba(0,0,0,0.2)',
                border: '1px solid rgba(0,0,0,0.1)',
                zIndex: 1000 // Ensure it stays above the map
            }}>
                <div style={{ fontWeight: 600, marginBottom: '6px', color: '#333' }}>
                    {palette.label}
                </div>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                }}>
                    <span style={{ color: '#666', fontWeight: 500 }}>{Math.round(minVal)}%</span>
                    <div style={{
                        width: '120px',
                        height: '12px',
                        borderRadius: '6px',
                        background: `linear-gradient(to right, ${palette.stops.join(', ')})`,
                        boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.1)',
                    }} />
                    <span style={{ color: '#666', fontWeight: 500 }}>{Math.round(maxVal)}%</span>
                </div>
            </div>
        </div>
    );
};

export default ActualHyderabadMap;
