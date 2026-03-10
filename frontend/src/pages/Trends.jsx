import React, { useState, useEffect } from 'react';
import { Search, Filter } from 'lucide-react';
import api from '../api/client';

const Trends = () => {
  const [exports, setExports] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchExports = async () => {
      try {
        const res = await api.get('/exports?limit=50');
        setExports(res.data);
      } catch (e) {
        console.error("Failed to fetch exports", e);
      } finally {
        setLoading(false);
      }
    };
    fetchExports();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Export Trends Data</h1>
        
        <div className="flex gap-2 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 h-4 w-4" />
            <input 
              type="text" 
              placeholder="Search by country or HS code..." 
              className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 flex-shrink-0">
            <Filter className="h-4 w-4" />
            <span>Filter</span>
          </button>
        </div>
      </div>

      <div className="bg-white border text-sm max-h-[600px] overflow-auto border-gray-200 rounded-xl shadow-sm">
        {loading ? (
           <div className="p-8 text-center text-gray-500">Loading data...</div>
        ) : (
          <table className="w-full text-left">
            <thead className="bg-gray-50 sticky top-0 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 font-medium text-gray-500">Year</th>
                <th className="px-6 py-3 font-medium text-gray-500">Country</th>
                <th className="px-6 py-3 font-medium text-gray-500">Product (HS)</th>
                <th className="px-6 py-3 font-medium text-gray-500">Value (USD)</th>
                <th className="px-6 py-3 font-medium text-gray-500">Volume (Tons)</th>
                <th className="px-6 py-3 font-medium text-gray-500">Anomaly</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {exports.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                    No records found or backend is offline.
                  </td>
                </tr>
              ) : (
                exports.map((row, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-6 py-4">{row.year}</td>
                    <td className="px-6 py-4 font-medium text-gray-900">
                      {row.country_name} <span className="text-gray-400 text-xs ml-1">{row.country_iso3}</span>
                    </td>
                    <td className="px-6 py-4">{row.product_name} ({row.hs_code})</td>
                    <td className="px-6 py-4">${row.value_usd.toLocaleString()}</td>
                    <td className="px-6 py-4">{row.volume_tons.toLocaleString()}</td>
                    <td className="px-6 py-4">
                      {row.anomaly_flag ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                          Flagged
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                          Normal
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default Trends;
