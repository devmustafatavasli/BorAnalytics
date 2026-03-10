import React from 'react';

const KPICard = ({ title, value, trend, icon }) => {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-sm font-medium text-gray-500 mb-1">{title}</p>
          <h3 className="text-2xl font-bold text-gray-900">{value}</h3>
          
          {trend && (
            <p className={`text-sm mt-2 flex items-center ${trend.value >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              <span className="font-semibold">{trend.value >= 0 ? '+' : ''}{trend.value}%</span>
              <span className="text-gray-500 ml-1"> {trend.label}</span>
            </p>
          )}
        </div>
        <div className="p-3 bg-primary-50 rounded-lg text-primary-600">
          {icon}
        </div>
      </div>
    </div>
  );
};

export default KPICard;
