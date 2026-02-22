import React, { useState, useRef, useCallback } from 'react';
import { ComposableMap, Geographies, Geography, ZoomableGroup } from "react-simple-maps";
import { scaleLinear } from "d3-scale";

const INDIA_GEO_URL = "/india.json";

const PROJECTION_CONFIG = {
    scale: 350,
    center: [82, 22]
};

// Color palettes for different map types
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

const IndiaMap = ({ data, mapType }) => {
    const [tooltip, setTooltip] = useState({ show: false, x: 0, y: 0, content: null });
    const containerRef = useRef(null);

    // Build data map: state name → { value, metadata }
    const dataMap = {};
    let minVal = Infinity, maxVal = -Infinity;
    if (data && data.data) {
        data.data.forEach(d => {
            dataMap[d.region] = {
                value: d.value,
                metadata: d.metadata || {}
            };
            if (d.value < minVal) minVal = d.value;
            if (d.value > maxVal) maxVal = d.value;
        });
    }
    if (minVal === Infinity) { minVal = 0; maxVal = 100; }

    const palette = COLOR_RANGES[mapType] || COLOR_RANGES.antibiotic_performance;

    // Create color scale
    const colorScale = scaleLinear()
        .domain(palette.stops.map((_, i) => minVal + (maxVal - minVal) * (i / (palette.stops.length - 1))))
        .range(palette.stops)
        .clamp(true);

    const handleMouseMove = useCallback((event) => {
        if (!containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        setTooltip(prev => ({
            ...prev,
            x: event.clientX - rect.left,
            y: event.clientY - rect.top
        }));
    }, []);

    const handleMouseEnter = useCallback((geo) => {
        const name = geo.properties.NAME_1 || geo.properties.st_nm || 'Unknown';
        const info = dataMap[name];

        let content;
        if (info) {
            content = {
                name,
                value: info.value,
                detail: info.metadata?.detail || `${info.value}%`,
                isolates: info.metadata?.isolates || null,
                info: info.metadata?.info || null
            };
        } else {
            content = {
                name,
                value: null,
                detail: 'No data available',
                pathogen: null
            };
        }
        setTooltip(prev => ({ ...prev, show: true, content }));
    }, [dataMap]);

    const handleMouseLeave = useCallback(() => {
        setTooltip(prev => ({ ...prev, show: false, content: null }));
    }, []);

    return (
        <div
            ref={containerRef}
            onMouseMove={handleMouseMove}
            style={{
                width: '100%',
                height: '500px',
                borderRadius: '8px',
                position: 'relative',
                overflow: 'hidden'
            }}
        >
            <ComposableMap
                projection="geoMercator"
                projectionConfig={PROJECTION_CONFIG}
                style={{ width: '100%', height: '100%' }}
                width={400}
                height={440}
            >
                <ZoomableGroup zoom={1} minZoom={0.8} maxZoom={4}>
                    <Geographies geography={INDIA_GEO_URL}>
                        {({ geographies }) =>
                            geographies.map(geo => {
                                const name = geo.properties.NAME_1 || geo.properties.st_nm;
                                const info = dataMap[name];
                                const fillColor = info
                                    ? colorScale(info.value)
                                    : '#e0e0e0';

                                return (
                                    <Geography
                                        key={geo.rsmKey}
                                        geography={geo}
                                        fill={fillColor}
                                        stroke="#ffffff"
                                        strokeWidth={0.4}
                                        style={{
                                            default: { outline: 'none', transition: 'fill 0.2s' },
                                            hover: {
                                                fill: '#ffd54f',
                                                outline: 'none',
                                                cursor: 'pointer',
                                                stroke: '#333',
                                                strokeWidth: 1.2
                                            },
                                            pressed: { outline: 'none' }
                                        }}
                                        onMouseEnter={() => handleMouseEnter(geo)}
                                        onMouseLeave={handleMouseLeave}
                                    />
                                );
                            })
                        }
                    </Geographies>
                </ZoomableGroup>
            </ComposableMap>

            {/* Cursor-following Tooltip */}
            {tooltip.show && tooltip.content && (
                <div
                    style={{
                        position: 'absolute',
                        left: tooltip.x + 12,
                        top: tooltip.y - 10,
                        background: 'rgba(30, 30, 46, 0.95)',
                        color: '#fff',
                        padding: '10px 14px',
                        borderRadius: '8px',
                        fontSize: '0.85rem',
                        lineHeight: 1.5,
                        pointerEvents: 'none',
                        zIndex: 100,
                        boxShadow: '0 4px 14px rgba(0,0,0,0.3)',
                        maxWidth: '220px',
                        backdropFilter: 'blur(8px)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        transform: 'translateY(-50%)'
                    }}
                >
                    <div style={{ fontWeight: 700, fontSize: '0.95rem', marginBottom: '4px', color: '#ffd54f' }}>
                        {tooltip.content.name}
                    </div>
                    {tooltip.content.value !== null ? (
                        <>
                            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px' }}>
                                <span style={{ opacity: 0.8 }}>Resistance:</span>
                                <span style={{ fontWeight: 600 }}>{tooltip.content.value}%</span>
                            </div>
                            {tooltip.content.isolates && (
                                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', marginTop: '2px' }}>
                                    <span style={{ opacity: 0.8 }}>Isolates:</span>
                                    <span style={{ fontWeight: 600 }}>{tooltip.content.isolates.toLocaleString()}</span>
                                </div>
                            )}
                            {tooltip.content.info && (
                                <div style={{ fontSize: '0.72rem', opacity: 0.6, marginTop: '4px', fontStyle: 'italic' }}>
                                    {tooltip.content.info}
                                </div>
                            )}
                        </>
                    ) : (
                        <div style={{ opacity: 0.6, fontStyle: 'italic' }}>No surveillance data</div>
                    )}
                </div>
            )}

            {/* Gradient Legend */}
            <div style={{
                position: 'absolute',
                bottom: '16px',
                right: '16px',
                background: 'rgba(255,255,255,0.95)',
                padding: '10px 14px',
                borderRadius: '8px',
                fontSize: '0.75rem',
                boxShadow: '0 2px 8px rgba(0,0,0,0.12)',
                border: '1px solid rgba(0,0,0,0.06)'
            }}>
                <div style={{ fontWeight: 600, marginBottom: '6px', color: '#333' }}>
                    {palette.label}
                </div>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                }}>
                    <span style={{ color: '#666' }}>{Math.round(minVal)}%</span>
                    <div style={{
                        width: '100px',
                        height: '10px',
                        borderRadius: '5px',
                        background: `linear-gradient(to right, ${palette.stops.join(', ')})`,
                    }} />
                    <span style={{ color: '#666' }}>{Math.round(maxVal)}%</span>
                </div>
            </div>
        </div>
    );
};

export default IndiaMap;
