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
      </div>
    </header>
  );
};

export default Navbar;
