import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

import "./styles/global.css";
import { ThemeProvider } from './styles/ThemeContext';
import MainLayout from './layouts/mainLayout';
import VoterLandingPage from './pages/voter/voterLandingPage';
import VoterAboutPage from '../../frontend/src/pages/voter/voterAboutPage';
import VoterRegistrationPage from '../../frontend/src/pages/voter/voterRegistrationPage';
import VoterVotingProcessPage from '../../frontend/src/pages/voter/voterVotingProcessPage';

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
            <Route path="/voter/about" element={<VoterAboutPage />} />
            <Route path="/voter/register" element={<VoterRegistrationPage />} />
            <Route path="/voter/voting-process" element={<VoterVotingProcessPage />} />

            {/* Official routes */}

            {/* Shared routes */}

          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
};

export default App;

