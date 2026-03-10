import React, { useState, useEffect } from 'react';
import { DollarSign, TrendingUp, Package, Globe } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend } from 'recharts';
import KPICard from '../components/KPICard';
import api from '../api/client';

const Overview = () => {
  const [data, setData] = useState({
    topDestinations: [],
    exportTrends: [],
    isLoading: true
  });

  useEffect(() => {
    const fetchDashboardData = async () => {
        try {
            // In a real app we'd fetch actual values, simulating top KPIs from api responses
            const [destRes, growthRes] = await Promise.all([
                api.get('/analytics/top-destinations?year=2023&limit=5'),
                api.get('/analytics/yoy-growth')
            ]);
            
            // Format for general export trend
            const trendData = growthRes.data.map(item => ({
                year: item.year,
                value: item.value_usd / 1000000 // Convert to millions
            }));

            setData({
                topDestinations: destRes.data,
                exportTrends: trendData,
                isLoading: false
            });
        } catch (error) {
            console.error("Failed to load dashboard data", error);
            setData(prev => ({ ...prev, isLoading: false }));
        }
    };
    
    fetchDashboardData();
  }, []);

  if (data.isLoading) return <div className="flex h-64 items-center justify-center">Loading dashboard...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard Overview</h1>
        <div className="flex gap-2">
            <select className="bg-white border text-sm rounded-lg block p-2">
                <option>2023</option>
                <option>2022</option>
                <option>2021</option>
            </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard 
          title="Total Export Value" 
          value="$1.24B" 
          trend={{ value: 12.5, label: 'vs last year' }} 
          icon={<DollarSign size={24} />} 
        />
        <KPICard 
          title="Total Volume" 
          value="2.4M Tons" 
          trend={{ value: 8.2, label: 'vs last year' }} 
          icon={<Package size={24} />} 
        />
        <KPICard 
          title="Active Markets" 
          value="114" 
          trend={{ value: 2, label: 'new this year' }} 
          icon={<Globe size={24} />} 
        />
        <KPICard 
          title="Avg Price / Ton" 
          value="$516" 
          trend={{ value: 4.1, label: 'vs last year' }} 
          icon={<TrendingUp size={24} />} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="text-lg font-bold mb-4">Export Value Trend (Millions USD)</h2>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.exportTrends} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="year" />
                <YAxis />
                <Tooltip formatter={(value) => [`$${value.toFixed(2)}M`, 'Value']} />
                <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={3} activeDot={{ r: 8 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="text-lg font-bold mb-4">Top 5 Destinations (2023)</h2>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart layout="vertical" data={data.topDestinations} margin={{ top: 5, right: 5, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false}/>
                <XAxis type="number" />
                <YAxis dataKey="country_name" type="category" width={80} tick={{fontSize: 12}} />
                <Tooltip formatter={(value) => [`$${(value/1000000).toFixed(2)}M`, 'Value']} />
                <Bar dataKey="value_usd" fill="#10b981" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Overview;
