// Main layout component for the e-voting platform

import React from "react";
import { Outlet } from "react-router-dom";
import { useTheme } from "../styles/ThemeContext";
import Navbar from "../components/navbar";

const MainLayout: React.FC = () => {
  const { theme } = useTheme();
  const { colors } = theme;

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
      <Navbar />

      <main style={{ flex: 1 }}>
        <Outlet />
      </main>
    </div>
  );
};

export default MainLayout;