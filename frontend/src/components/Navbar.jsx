import React from 'react';
import { Activity } from 'lucide-react';

const Navbar = () => {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-30">
      <div className="flex h-16 items-center px-4 md:px-6">
        <div className="flex items-center gap-2 font-bold text-xl text-primary-600">
          <Activity className="h-6 w-6" />
          <span>BorAnalytics</span>
        </div>
        <nav className="ml-8 hidden md:flex items-center gap-6 text-sm font-medium text-gray-500">
          <a href="/" className="hover:text-primary-600 transition-colors">Overview</a>
          <a href="/trends" className="hover:text-primary-600 transition-colors">Trends</a>
          <a href="/map" className="hover:text-primary-600 transition-colors">Trade Map</a>
          <a href="/market" className="hover:text-primary-600 transition-colors">Market Share</a>
          <a href="/predictions" className="hover:text-primary-600 transition-colors">Predictions</a>
          <a href="/network" className="text-primary-600 hover:text-primary-700 transition-colors">Trade Network</a>
        </nav>
      </div>
    </header>
  );
};

export default Navbar;
