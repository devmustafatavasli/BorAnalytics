import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import api from '../api/client';

const Market = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMarketShare = async () => {
      try {
        const res = await api.get('/analytics/market-share');
        // Format for Area Chart (stacked percentages)
        const formatted = res.data.map(d => ({
          year: d.year.toString(),
          turkey_share: Number(d.turkey_share_pct.toFixed(2)),
          row_share: Number(d.row_share_pct.toFixed(2))
        }));
        setData(formatted);
      } catch (e) {
        console.error("Market share fetch error", e);
      } finally {
        setLoading(false);
      }
    };
    fetchMarketShare();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Market Intelligence</h1>
          <p className="text-gray-500 mt-1">Boron global market share analysis (Turkey vs ROW)</p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <h2 className="text-xl font-bold mb-6">Market Share Evolution (%)</h2>
        
        {loading ? (
          <div className="h-96 flex items-center justify-center text-gray-500">Loading chart data...</div>
        ) : data.length === 0 ? (
          <div className="h-96 flex items-center justify-center text-gray-500 bg-gray-50 rounded-lg border border-dashed">
            No market share data available from the backend.
          </div>
        ) : (
          <div className="h-96 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorTurkey" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorRow" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="year" />
                <YAxis tickFormatter={(tick) => `${tick}%`} />
                <Tooltip />
                <Legend verticalAlign="top" height={36}/>
                <Area 
                  type="monotone" 
                  dataKey="row_share" 
                  name="Rest of World" 
                  stackId="1" 
                  stroke="#3b82f6" 
                  fillOpacity={1} 
                  fill="url(#colorRow)" 
                />
                <Area 
                  type="monotone" 
                  dataKey="turkey_share" 
                  name="Turkey" 
                  stackId="1" 
                  stroke="#ef4444" 
                  fillOpacity={1} 
                  fill="url(#colorTurkey)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
};

export default Market;
