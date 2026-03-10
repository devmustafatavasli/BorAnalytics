import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Overview from './pages/Overview';
import Trends from './pages/Trends';
import TradeMap from './pages/TradeMap';
import Predictions from './pages/Predictions';
import Market from './pages/Market';

// Lazy-load heavy pages to prevent runtime crashes from killing the entire app
const NetworkPage = React.lazy(() => import('./pages/NetworkPage'));
const AskPage = React.lazy(() => import('./pages/AskPage'));

const PageLoader = () => (
  <div className="flex items-center justify-center h-64 text-gray-500">Loading page...</div>
);

function App() {
  return (
    <Router>
      <Layout>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/trends" element={<Trends />} />
            <Route path="/map" element={<TradeMap />} />
            <Route path="/predictions" element={<Predictions />} />
            <Route path="/market" element={<Market />} />
            <Route path="/network" element={<NetworkPage />} />
            <Route path="/ask" element={<AskPage />} />
          </Routes>
        </Suspense>
      </Layout>
    </Router>
  );
}

export default App;
