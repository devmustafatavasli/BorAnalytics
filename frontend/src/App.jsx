import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Overview from './pages/Overview';
import Trends from './pages/Trends';
import TradeMap from './pages/TradeMap';
import Predictions from './pages/Predictions';
import Market from './pages/Market';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/trends" element={<Trends />} />
          <Route path="/map" element={<TradeMap />} />
          <Route path="/predictions" element={<Predictions />} />
          <Route path="/market" element={<Market />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
