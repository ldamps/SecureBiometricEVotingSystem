import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';

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
import OfficialProfilePage from './pages/official/officialProfilePage';
import OfficialOnboardingPage from './pages/official/officialOnboardingPage';
import ManageElectionsPage from './pages/official/manageElectionsPage';
import ManageReferendumsPage from './pages/official/manageReferendumsPage';

// Authenticator PWA layout
import AuthenticatorLayout from './layouts/authenticatorLayout';

// Biometric pages — lazy-loaded so face-api.js / TensorFlow.js
// are only downloaded when the user navigates to a biometric route.
const MobileEnrollPage = React.lazy(() => import('./pages/biometric/mobileEnrollPage'));
const MobileVerifyPage = React.lazy(() => import('./pages/biometric/mobileVerifyPage'));

// Authenticator PWA pages (built-in QR scanner flow)
const AuthHomePage = React.lazy(() => import('./pages/auth/authHomePage'));
const AuthEnrollPage = React.lazy(() => import('./pages/auth/authEnrollPage'));
const AuthVerifyPage = React.lazy(() => import('./pages/auth/authVerifyPage'));

/**
 * Check if the PWA was opened from the home screen and a biometric
 * page saved a redirect URL before install.  If so, navigate there
 * so the user resumes enrollment/verification without re-scanning.
 */
function PwaRedirect() {
  // If running as an installed PWA, go to the authenticator QR scanner.
  if (typeof window !== "undefined") {
    const standalone = (navigator as any).standalone === true ||
      window.matchMedia("(display-mode: standalone)").matches;
    if (standalone) return <Navigate to="/auth" replace />;
  }
  return <Navigate to="/voter/landing" replace />;
}

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          {/* Authenticator PWA routes — chromeless layout with built-in QR scanner */}
          <Route element={<AuthenticatorLayout />}>
            <Route path="/auth" element={<Suspense fallback={<div style={{padding:"2rem",textAlign:"center"}}>Loading…</div>}><AuthHomePage /></Suspense>} />
            <Route path="/auth/enroll" element={<Suspense fallback={<div style={{padding:"2rem",textAlign:"center"}}>Loading enrollment…</div>}><AuthEnrollPage /></Suspense>} />
            <Route path="/auth/verify" element={<Suspense fallback={<div style={{padding:"2rem",textAlign:"center"}}>Loading verification…</div>}><AuthVerifyPage /></Suspense>} />
          </Route>

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
                <Route path="profile" element={<OfficialProfilePage />} />
                <Route path="onboarding" element={<OfficialOnboardingPage />} />
                <Route path="elections" element={<ManageElectionsPage />} />
                <Route path="referendums" element={<ManageReferendumsPage />} />
              </Route>
            </Route>
            
            {/* Mobile biometric routes (accessed via QR code on phone/tablet) */}
            <Route path="/biometric/enroll" element={<Suspense fallback={<div style={{padding:"2rem",textAlign:"center"}}>Loading biometric enrollment…</div>}><MobileEnrollPage /></Suspense>} />
            <Route path="/biometric/verify" element={<Suspense fallback={<div style={{padding:"2rem",textAlign:"center"}}>Loading biometric verification…</div>}><MobileVerifyPage /></Suspense>} />

            {/* Default route — resume biometric flow if PWA was installed, else landing */}
            <Route path="/" element={<PwaRedirect />} />
            <Route path="*" element={<Navigate to="/voter/landing" replace />} />

          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
};

export default App;

