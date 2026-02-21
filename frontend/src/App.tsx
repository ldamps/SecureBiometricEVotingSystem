import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

import "./styles/global.css";
import { ThemeProvider } from './styles/ThemeContext';
import MainLayout from './layouts/mainLayout';
import VoterLandingPage from './pages/voter/voterLandingPage';

// Voter pages

// Official pages

// Shared pages

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<MainLayout />}>

            {/* Voter routes */}
            <Route path="/voter/landing" element={<VoterLandingPage />} />

            {/* Official routes */}

            {/* Shared routes */}

          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
};

export default App;

