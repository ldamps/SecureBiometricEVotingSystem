import React from 'react';
import { BrowserRouter, Routes, Route, Outlet } from 'react-router-dom';

import "./styles/global.css";
import { ThemeProvider } from './styles/ThemeContext';
import MainLayout from './layouts/mainLayout';
import OfficialAuthGuard from './components/officialAuthGuard';

// Voter pages:
import VoterLandingPage from './pages/voter/voterLandingPage';
import VoterAboutPage from './pages/voter/voterAboutPage';
import VoterRegistrationPage from './pages/voter/voterRegistrationPage';
import VoterVotingProcessPage from './pages/voter/voterVotingProcessPage';
import VoterManageRegistrationPage from './pages/voter/voterManageRegistrationPage';
import VoterCastingPage from './pages/voter/voterVotingPage';
import VoteCastingPage from './pages/voter/voteCastingPage';
import VoterRegisterPage from './pages/voter/voterRegisterPage';
import VoterUpdateRegistrationPage from './pages/voter/voterUpdateRegistrationPage';

// Official pages
import OfficialLandingPage from './pages/official/officialLandingPage';
import OfficialHomePage from './pages/official/officialHomePage';

// Mobile biometric pages (accessed via QR code from phone/tablet)
import MobileEnrollPage from './pages/biometric/mobileEnrollPage';
import MobileVerifyPage from './pages/biometric/mobileVerifyPage';

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
            <Route path="/voter/registration" element={<VoterRegisterPage />} />
            <Route path="/voter/update-registration" element={<VoterUpdateRegistrationPage />} />
            
            {/* Official routes: landing is public; all other /official/* require login */}
            <Route path="official" element={<Outlet />}>
              <Route path="landing" element={<OfficialLandingPage />} />
              <Route element={<OfficialAuthGuard />}>
                <Route path="home" element={<OfficialHomePage />} />
              </Route>
            </Route>
            
            {/* Mobile biometric routes (accessed via QR code on phone/tablet) */}
            <Route path="/biometric/enroll" element={<MobileEnrollPage />} />
            <Route path="/biometric/verify" element={<MobileVerifyPage />} />

            {/* Shared routes */}

          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
};

export default App;

