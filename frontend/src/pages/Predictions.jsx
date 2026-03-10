import React, { useState } from 'react';
import { ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Search } from 'lucide-react';
import api from '../api/client';

const Predictions = () => {
  const [productCode, setProductCode] = useState('2528');
  const [countryIso, setCountryIso] = useState('CHN');
  const [horizon, setHorizon] = useState(3);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchPrediction = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`/predictions/demand?product_hs_code=${productCode}&country_iso3=${countryIso}&horizon=${horizon}`);
      
      const formatted = res.data.forecasts.map(f => ({
        year: f.year,
        predicted: f.predicted_value,
        ci: [f.lower_ci, f.upper_ci] // Range for Area component
      }));
      
      setData({
        ...res.data,
        chartData: formatted
      });
    } catch (err) {
      console.error(err);
      setError("Prediction not found or error loading model data.");
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Demand Predictions (LSTM)</h1>
      
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
        <form onSubmit={fetchPrediction} className="flex flex-col md:flex-row gap-4 items-end">
          <div className="flex-1 w-full">
            <label className="block text-sm font-medium text-gray-700 mb-1">Product HS Code</label>
            <input 
              type="text" 
              value={productCode}
              onChange={(e) => setProductCode(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div className="flex-1 w-full">
            <label className="block text-sm font-medium text-gray-700 mb-1">Country ISO3</label>
            <input 
              type="text" 
              value={countryIso}
              onChange={(e) => setCountryIso(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div className="w-32">
            <label className="block text-sm font-medium text-gray-700 mb-1">Horizon (Years)</label>
            <select 
              value={horizon}
              onChange={(e) => setHorizon(Number(e.target.value))}
              className="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value={1}>1 Year</option>
              <option value={3}>3 Years</option>
              <option value={5}>5 Years</option>
            </select>
          </div>
          <button 
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? 'Running...' : <><Search size={18} /> Forecast</>}
          </button>
        </form>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200">
          {error}
        </div>
      )}

      {data && !loading && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
              <p className="text-sm text-gray-500">Target Area</p>
              <p className="text-lg font-bold">{data.country_name} ({data.product_name})</p>
            </div>
            <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
              <p className="text-sm text-gray-500">Model Metric (MAE)</p>
              <p className="text-lg font-bold text-blue-600">{data.mae.toFixed(2)}</p>
            </div>
            <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
              <p className="text-sm text-gray-500">Model Metric (RMSE)</p>
              <p className="text-lg font-bold text-indigo-600">{data.rmse.toFixed(2)}</p>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <h2 className="text-lg font-bold mb-6">Predicted Demand Volume (Tons)</h2>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={data.chartData} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="year" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area type="monotone" dataKey="ci" name="90% Confidence Interval" fill="#8884d8" fillOpacity={0.3} stroke="none" />
                  <Line type="monotone" dataKey="predicted" name="Forecast Volume" stroke="#3b82f6" strokeWidth={3} dot={{ r: 6 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Predictions;
