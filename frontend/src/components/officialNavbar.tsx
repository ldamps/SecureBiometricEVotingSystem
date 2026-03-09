import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useTheme } from "../styles/ThemeContext";

const OfficialNavbar: React.FC = () => {
  const { theme, mode, toggleTheme } = useTheme();
  const { colors, spacing, fontSizes, fontWeights, layout } = theme;
  const [showInfo, setShowInfo] = useState(false);

  return (
    <nav
      className="app-nav"
      style={{
        position: "sticky",
        top: 0,
        zIndex: 200,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        height: "72px",
        backgroundColor: colors.navBackground,
        color: colors.navText,
        transition: "background-color 0.3s ease",
      }}
    >
      <Link
        to="/official/home"
        className="nav-brand"
        style={{
          color: colors.navText,
          textDecoration: "none",
          fontWeight: fontWeights.bold,
          letterSpacing: "0.02em",
        }}
      >
        Election Official Portal
      </Link>

      {/* Right side: theme toggle + info button */}
      <div style={{ display: "flex", alignItems: "center", gap: spacing.md }}>
        {/* Light/Dark mode toggle */}
        <button
          onClick={toggleTheme}
          aria-label="Toggle theme"
          title={mode === "light" ? "Switch to Dark Mode" : "Switch to Light Mode"}
          style={{
            padding: "0",
            backgroundColor: "transparent",
            border: "none",
            color: colors.navText,
            fontSize: fontSizes["4xl"],
            cursor: "pointer",
            whiteSpace: "nowrap",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {mode === "light" ? (
              <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke={colors.navText} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z" />
              </svg>
            ) : (
              <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke={colors.navText} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="5" />
                <line x1="12" y1="1" x2="12" y2="3" />
                <line x1="12" y1="21" x2="12" y2="23" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="1" y1="12" x2="3" y2="12" />
                <line x1="21" y1="12" x2="23" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
            )}
        </button>
      </div>
    </nav>
  );
};

export default OfficialNavbar;