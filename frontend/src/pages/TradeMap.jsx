import React, { useState, useEffect } from 'react';
import { ComposableMap, Geographies, Geography, ZoomableGroup } from 'react-simple-maps';
import { scaleLinear } from 'd3-scale';
import { Tooltip } from 'react-tooltip';
import api from '../api/client';

const geoUrl = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

const TradeMap = () => {
  const [data, setData] = useState([]);
  const [metric, setMetric] = useState('value_usd');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMapData = async () => {
      try {
        setLoading(true);
        // Fetch exports data for the latest year to populate the map
        const res = await api.get('/exports?year=2023&limit=1000');
        
        // Aggregate by country since exports can have multiple products per country
        const aggregated = res.data.reduce((acc, curr) => {
            if (!acc[curr.country_iso3]) {
                acc[curr.country_iso3] = {
                    iso3: curr.country_iso3,
                    name: curr.country_name,
                    value_usd: 0,
                    volume_tons: 0
                };
            }
            acc[curr.country_iso3].value_usd += curr.value_usd;
            acc[curr.country_iso3].volume_tons += curr.volume_tons;
            return acc;
        }, {});
        
        setData(Object.values(aggregated));
        setLoading(false);
      } catch (err) {
        console.error("Failed to fetch map data", err);
        setLoading(false);
      }
    };
    fetchMapData();
  }, []);

  const maxValue = data.length > 0 ? Math.max(...data.map(d => d[metric])) : 1;

  const colorScale = scaleLinear()
    .domain([0, maxValue])
    .range(["#dbeafe", "#1e3a8a"]); // Light blue to dark blue

  return (
    <div className="space-y-6 flex flex-col h-full bg-slate-50 relative">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Global Trade Map</h1>
        <select 
          className="bg-white border border-gray-300 text-sm rounded-lg p-2"
          value={metric}
          onChange={(e) => setMetric(e.target.value)}
        >
            <option value="value_usd">Value (USD)</option>
            <option value="volume_tons">Volume (Tons)</option>
        </select>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm flex-1 overflow-hidden relative">
        <div className="absolute top-4 right-4 bg-white/90 p-3 rounded-lg border text-sm z-10 shadow-sm cursor-default">
            <p className="font-bold mb-2">Export {metric === 'value_usd' ? 'Value' : 'Volume'}</p>
            <div className="flex items-center gap-2"><div className="w-4 h-4 rounded bg-[#dbeafe]"></div> Low</div>
            <div className="flex items-center gap-2 mt-1"><div className="w-4 h-4 rounded bg-[#1e3a8a]"></div> High</div>
        </div>
        
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/50 z-20">
             <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}

        <ComposableMap projection="geoMercator" projectionConfig={{ scale: 120 }}>
          <ZoomableGroup center={[0, 20]} zoom={1} minZoom={1} maxZoom={8}>
            <Geographies geography={geoUrl}>
              {({ geographies }) =>
                geographies.map((geo) => {
                  const countryIdentifier = geo.id || geo.properties.iso_a3;
                  const d = data.find((s) => s.iso3 === countryIdentifier);
                  
                  let fill = "#F5F4F6";
                  if (countryIdentifier === "TUR") {
                    fill = "#ef4444"; // Red for source
                  } else if (d) {
                    fill = colorScale(d[metric]);
                  }

                  return (
                    <Geography
                      key={geo.rsmKey}
                      geography={geo}
                      fill={fill}
                      stroke="#d1d5db"
                      strokeWidth={0.5}
                      data-tooltip-id="map-tooltip"
                      data-tooltip-content={
                        countryIdentifier === "TUR" 
                          ? "Turkey (Source)" 
                          : d 
                            ? `${d.name}: ${metric === 'value_usd' ? '$' + (d.value_usd/1000000).toFixed(2) + 'M' : d.volume_tons.toLocaleString() + ' Tons'}`
                            : `${geo.properties.name || countryIdentifier}: No Data`
                      }
                      style={{
                        default: { outline: "none" },
                        hover: { fill: "#f59e0b", outline: "none", cursor: d ? "pointer" : "default" },
                        pressed: { outline: "none" },
                      }}
                    />
                  );
                })
              }
            </Geographies>
          </ZoomableGroup>
        </ComposableMap>
        <Tooltip id="map-tooltip" className="z-50" />
      </div>
    </div>
  );
};

export default TradeMap;
