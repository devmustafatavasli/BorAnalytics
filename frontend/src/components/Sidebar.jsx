import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, TrendingUp, Globe, Brain, PieChart } from 'lucide-react';

const Sidebar = ({ className = '' }) => {
  const links = [
    { to: '/', icon: <LayoutDashboard size={20} />, label: 'Overview' },
    { to: '/trends', icon: <TrendingUp size={20} />, label: 'Trends' },
    { to: '/map', icon: <Globe size={20} />, label: 'Trade Map' },
    { to: '/predictions', icon: <Brain size={20} />, label: 'Predictions' },
    { to: '/market', icon: <PieChart size={20} />, label: 'Market Intelligence' },
  ];

  return (
    <aside className={`bg-white border-r border-gray-200 flex flex-col ${className}`}>
      <nav className="flex-1 overflow-y-auto p-4 space-y-2">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${
                isActive 
                  ? 'bg-primary-50 text-primary-600 font-medium' 
                  : 'text-gray-600 hover:bg-gray-100'
              }`
            }
          >
            {link.icon}
            <span>{link.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
