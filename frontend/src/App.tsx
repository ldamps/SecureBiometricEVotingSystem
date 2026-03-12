import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

import "./styles/global.css";
import { ThemeProvider } from './styles/ThemeContext';
import MainLayout from './layouts/mainLayout';

// Voter pages:
import VoterLandingPage from './pages/voter/voterLandingPage';
import VoterAboutPage from '../../frontend/src/pages/voter/voterAboutPage';
import VoterRegistrationPage from '../../frontend/src/pages/voter/voterRegistrationPage';
import VoterVotingProcessPage from '../../frontend/src/pages/voter/voterVotingProcessPage';
import VoterManageRegistrationPage from '../../frontend/src/pages/voter/voterManageRegistrationPage';
import VoterCastingPage from './pages/voter/voterVotingPage';
import VoteCastingPage from './pages/voter/voteCastingPage';
import VoterRegisterPage from './pages/voter/voterRegisterPage';
import VoterUpdateRegistrationPage from './pages/voter/voterUpdateRegistrationPage';

// Official pages
import OfficialLandingPage from './pages/official/officialLandingPage';
import OfficialHomePage from './pages/official/officialHomePage';

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
            <Route path="/voter/manage-registration" element={<VoterManageRegistrationPage />} />
            <Route path="/voter/voting" element={<VoterCastingPage />} />
            <Route path="/voter/vote-casting" element={<VoteCastingPage />} />  
            <Route path="/voter/registeration" element={<VoterRegisterPage />} />
            <Route path="/voter/update-registration" element={<VoterUpdateRegistrationPage />} />
            
            {/* Official routes */}
            <Route path="/official/landing" element={<OfficialLandingPage />} />
            <Route path="/official/home" element={<OfficialHomePage />} />
            
            {/* Shared routes */}

          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
};

export default App;

