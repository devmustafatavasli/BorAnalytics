import React, { useState, useEffect, useRef } from 'react';
import { ForceGraph2D } from 'react-force-graph';
import api from '../api/client';

const EVENT_TYPE_COLORS = {
  capacity_expansion: '#27AE60',
  export_agreement: '#2E74B5',
  facility_opening: '#16A085',
  production_announcement: '#7F8C8D',
  reserve_update: '#E67E22',
  regulatory_change: '#E74C3C'
};

const NetworkPage = () => {
    const [graphData, setGraphData] = useState({ nodes: [], links: [] });
    const [centrality, setCentrality] = useState([]);
    const [selectedCountry, setSelectedCountry] = useState(null);
    const [exposure, setExposure] = useState(null);
    const [events, setEvents] = useState([]);
    const [selectedEvent, setSelectedEvent] = useState(null);
    const [eventImpact, setEventImpact] = useState([]);
    
    const [loadingGraph, setLoadingGraph] = useState(true);
    const [graphError, setGraphError] = useState(false);
    
    // Resize wrapper safely
    const wrapRef = useRef();
    const [dims, setDims] = useState({ width: 600, height: 400 });
    
    useEffect(() => {
        if(wrapRef.current) {
            setDims({ width: wrapRef.current.clientWidth, height: wrapRef.current.clientHeight || 400 });
        }
    }, [wrapRef.current]);

    useEffect(() => {
        const fetchGraph = async () => {
            try {
                const res = await api.get('/graph/centrality');
                const data = res.data;
                setCentrality(data);
                
                const nodes = [{ id: 'TUR', name: 'Turkey', val: 10 }];
                const links = [];
                
                data.forEach(c => {
                    nodes.push({ id: c.iso3, name: c.name, val: Math.log(c.total_received + 1) });
                    links.push({ source: 'TUR', target: c.iso3, value: c.total_received });
                });
                
                setGraphData({ nodes, links });
                setLoadingGraph(false);
            } catch (err) {
                if(err.response?.status === 503) setGraphError(true);
                setLoadingGraph(false);
            }
        };
        fetchGraph();
        
        const fetchEvents = async () => {
            try {
                const res = await api.get('/events');
                setEvents(res.data);
            } catch(e) {}
        };
        fetchEvents();
    }, []);

    useEffect(() => {
        if (!selectedCountry) {
            setExposure(null);
            return;
        }
        const fetchExp = async () => {
            try {
                const res = await api.get(`/graph/exposure?country=${selectedCountry}`);
                setExposure(res.data);
            } catch(e) {}
        };
        fetchExp();
    }, [selectedCountry]);
    
    const openEventModal = async (ev) => {
        setSelectedEvent(ev);
        try {
            const res = await api.get(`/graph/event-impact?event_id=${ev.id}`);
            setEventImpact(res.data);
        } catch(e) {
            setEventImpact([]);
        }
    };

    if (graphError) {
        return (
            <div className="p-8 text-center text-red-600 font-semibold bg-red-50 rounded shadow m-4">
                Graph database not available in this environment. (NEO4J_URI not configured natively).
            </div>
        );
    }

    return (
        <div className="p-4 md:p-6 space-y-6">
            <h1 className="text-2xl font-bold text-gray-800">Global Boron Trade Network</h1>
            
            <div className="flex flex-col lg:flex-row gap-6">
                {/* Left Panel: Force Graph */}
                <div className="lg:w-3/5 border rounded-lg shadow-sm bg-white overflow-hidden" ref={wrapRef} style={{minHeight: '400px'}}>
                    {loadingGraph ? (
                        <div className="flex justify-center items-center h-full">Loading Network Nodes...</div>
                    ) : (
                        graphData.nodes.length > 0 && (
                            <ForceGraph2D
                                width={dims.width}
                                height={dims.height}
                                graphData={graphData}
                                nodeColor={n => n.id === 'TUR' ? '#F4D03F' : '#2E74B5'}
                                nodeVal={n => n.val}
                                nodeLabel="name"
                                linkWidth={l => Math.log((l.value/1000000) + 1)}
                                onNodeClick={n => {
                                    if(n.id !== 'TUR') setSelectedCountry(n.id);
                                }}
                            />
                        )
                    )}
                </div>

                {/* Right Panel: Exposure / Ranking */}
                <div className="lg:w-2/5 border rounded-lg shadow-sm bg-white p-4 overflow-y-auto max-h-[600px]">
                    {!selectedCountry ? (
                        <>
                            <h2 className="font-bold text-lg mb-4 text-gray-700">Top Dependant Importers</h2>
                            <table className="w-full text-sm text-left">
                                <thead className="bg-gray-50 border-b">
                                    <tr>
                                        <th className="py-2 px-2">Rank</th>
                                        <th className="py-2 px-2">Country</th>
                                        <th className="py-2 px-2">Total Vol (USD)</th>
                                        <th className="py-2 px-2">Years Active</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {centrality.slice(0, 15).map((c, i) => (
                                        <tr key={c.iso3} className="border-b hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedCountry(c.iso3)}>
                                            <td className="py-2 px-2">{i+1}</td>
                                            <td className="py-2 px-2 font-medium">{c.name}</td>
                                            <td className="py-2 px-2">${(c.total_received / 1e6).toFixed(1)}M</td>
                                            <td className="py-2 px-2">{c.years_active} years</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </>
                    ) : (
                        <div>
                            <button onClick={() => setSelectedCountry(null)} className="text-sm text-blue-600 mb-4">&larr; Back to rankings</button>
                            {exposure ? (
                                <div className="space-y-4">
                                    <h2 className="font-bold text-xl">{centrality.find(c=>c.iso3===selectedCountry)?.name || selectedCountry}</h2>
                                    <div className="bg-gray-50 p-4 rounded border">
                                        <p className="text-gray-500 text-sm">Total Turkish Imports</p>
                                        <p className="font-semibold text-lg">${(exposure.total_from_turkey / 1e6).toFixed(2)} Million</p>
                                    </div>
                                    <div className="bg-gray-50 p-4 rounded border">
                                        <p className="text-gray-500 text-sm">Average Annual Value</p>
                                        <p className="font-semibold text-lg">${(exposure.avg_annual_value / 1e6).toFixed(2)} Million</p>
                                    </div>
                                    <div className="bg-gray-50 p-4 rounded border">
                                        <p className="text-gray-500 text-sm">Active Trading Years</p>
                                        <p className="font-semibold text-lg">{exposure.years_trading} Years</p>
                                    </div>
                                    <div className="pt-2">
                                        <p className="text-gray-600 mb-2 font-medium">Products Dependent On:</p>
                                        <div className="flex flex-wrap gap-2">
                                            {exposure.products_imported.map(p => (
                                                <span key={p} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full font-bold">HS {p}</span>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div>Loading structural statistics...</div>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* Bottom Row: Events Timeline */}
            <div className="border rounded-lg shadow-sm bg-white p-4">
                <h2 className="font-bold text-xl mb-4 text-gray-800">Eti Maden Structural Events</h2>
                <div className="flex overflow-x-auto gap-4 pb-4 snap-x">
                    {events.map((ev) => (
                        <div key={ev.id} onClick={() => openEventModal(ev)} className="min-w-[280px] p-4 bg-gray-50 border rounded-lg snap-start cursor-pointer hover:shadow-md transition-shadow">
                            <span className="text-xs px-2 py-1 text-white rounded-full uppercase" style={{backgroundColor: EVENT_TYPE_COLORS[ev.event_type] || '#333'}}>
                                {ev.event_type.replace('_', ' ')}
                            </span>
                            <p className="font-bold mt-2 text-sm">{ev.title}</p>
                            <p className="text-gray-500 text-xs mt-1">{ev.event_year} • Magnitude: {ev.magnitude}</p>
                        </div>
                    ))}
                    {events.length === 0 && <p className="text-gray-500 text-sm">No structural events mapped natively to DB.</p>}
                </div>
            </div>

            {/* Impact Modal Overlay */}
            {selectedEvent && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
                    <div className="bg-white rounded-lg shadow-xl w-11/12 max-w-4xl max-h-[90vh] flex flex-col">
                        <div className="p-4 border-b flex justify-between items-center bg-gray-50">
                            <div>
                                <h3 className="font-bold text-lg">{selectedEvent.title}</h3>
                                <p className="text-sm text-gray-500">Post-Event Global Trade Impact</p>
                            </div>
                            <button onClick={() => setSelectedEvent(null)} className="font-bold text-xl text-gray-400 hover:text-black">&times;</button>
                        </div>
                        <div className="p-4 overflow-y-auto">
                            {eventImpact.length > 0 ? (
                                <table className="w-full text-sm text-left border">
                                    <thead className="bg-gray-100 border-b">
                                        <tr>
                                            <th className="py-2 px-3">Country</th>
                                            <th className="py-2 px-3 text-right">Pre-Event Vol (Y-1)</th>
                                            <th className="py-2 px-3 text-right">Post-Event Vol (Y)</th>
                                            <th className="py-2 px-3 text-right">Delta %</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {eventImpact.map((r) => (
                                            <tr key={r.iso3} className={`border-b ${r.pct_change > 15 ? 'bg-green-50' : r.pct_change < -15 ? 'bg-red-50' : ''}`}>
                                                <td className="py-2 px-3 font-medium">{r.name}</td>
                                                <td className="py-2 px-3 text-right">${(r.before_value / 1e6).toFixed(2)}M</td>
                                                <td className="py-2 px-3 text-right">${(r.after_value / 1e6).toFixed(2)}M</td>
                                                <td className={`py-2 px-3 text-right font-bold ${r.pct_change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                    {r.pct_change > 0 ? '+' : ''}{r.pct_change.toFixed(1)}%
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            ) : (
                                <p className="text-gray-500 text-center py-8">Insufficient temporal data to establish causal mapping limits for this event organically.</p>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default NetworkPage;
