import React from 'react';

const Footer = () => {
  return (
    <footer className="bg-white border-t border-gray-200 py-4 text-center text-sm text-gray-500 mt-auto">
      <p>&copy; {new Date().getFullYear()} BorAnalytics Project.</p>
    </footer>
  );
};

export default Footer;
