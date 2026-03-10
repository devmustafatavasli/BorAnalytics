import React, { useState, useEffect } from 'react';
import { ComposableMap, Geographies, Geography, ZoomableGroup } from 'react-simple-maps';
import { scaleLinear } from 'd3-scale';

const geoUrl = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

// Simulated fetch function until API mapping is fully wired
const fetchMapData = () => {
    return [
        { iso3: "CHN", value: 150000 },
        { iso3: "USA", value: 120000 },
        { iso3: "IND", value: 80000 },
        { iso3: "DEU", value: 65000 },
        { iso3: "BRA", value: 40000 }
    ];
};

const TradeMap = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    // In production: api.get('/analytics/map-data')
    setData(fetchMapData());
  }, []);

  const colorScale = scaleLinear()
    .domain([0, 150000])
    .range(["#dbeafe", "#1e3a8a"]); // Light blue to dark blue

  return (
    <div className="space-y-6 flex flex-col h-full bg-slate-50">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Global Trade Map</h1>
        <select className="bg-white border border-gray-300 text-sm rounded-lg p-2">
            <option>Volume (Tons)</option>
            <option>Value (USD)</option>
        </select>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm flex-1 overflow-hidden relative">
        <div className="absolute top-4 right-4 bg-white/90 p-3 rounded-lg border text-sm z-10 shadow-sm">
            <p className="font-bold mb-2">Export Volume</p>
            <div className="flex items-center gap-2"><div className="w-4 h-4 rounded bg-[#dbeafe]"></div> Low</div>
            <div className="flex items-center gap-2 mt-1"><div className="w-4 h-4 rounded bg-[#1e3a8a]"></div> High</div>
        </div>

        <ComposableMap projection="geoMercator" projectionConfig={{ scale: 120 }}>
          <ZoomableGroup center={[0, 20]} zoom={1} minZoom={1} maxZoom={8}>
            <Geographies geography={geoUrl}>
              {({ geographies }) =>
                geographies.map((geo) => {
                  const countryIdentifier = geo.id || geo.properties.iso_a3; // Depending on GeoJSON spec
                  const d = data.find((s) => s.iso3 === countryIdentifier);
                  
                  // Default gray if no data, color scale if data exists
                  // Special highlight for Turkey (TUR)
                  let fill = "#F5F4F6";
                  if (countryIdentifier === "TUR") {
                    fill = "#ef4444"; // Red for source
                  } else if (d) {
                    fill = colorScale(d.value);
                  }

                  return (
                    <Geography
                      key={geo.rsmKey}
                      geography={geo}
                      fill={fill}
                      stroke="#d1d5db"
                      strokeWidth={0.5}
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
      </div>
    </div>
  );
};

export default TradeMap;
