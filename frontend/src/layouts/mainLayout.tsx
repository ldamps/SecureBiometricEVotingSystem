// Main layout component for the e-voting platform

import React from "react";
import { Outlet, useLocation } from "react-router-dom";
import { useTheme } from "../styles/ThemeContext";
import Navbar from "../components/navbar";

const MainLayout: React.FC = () => {
  const { theme } = useTheme();
  const { colors } = theme;
  const { pathname } = useLocation();
  const isOfficialLanding = pathname === "/official/landing";
  const isOfficialHome = pathname === "/official/home";

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        backgroundColor: colors.background,
        color: colors.text.primary,
        transition: "background-color 0.3s ease, color 0.3s ease",
      }}
    >
      {!isOfficialLanding && !isOfficialHome && <Navbar />}

      <main style={{ flex: 1 }}>
        <Outlet />
      </main>
    </div>
  );
};

export default MainLayout;