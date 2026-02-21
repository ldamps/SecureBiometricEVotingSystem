// Navbar component for the e-voting platform

import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useTheme } from "../styles/ThemeContext";

const Navbar: React.FC = () => {
  const { theme, mode, toggleTheme } = useTheme();
  const { colors, spacing, fontSizes, fontWeights, layout } = theme;
  const [showInfo, setShowInfo] = useState(false);

  return (
    <nav
      style={{
        position: "sticky",
        top: 0,
        zIndex: 100,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        height: layout.navHeight,
        padding: `0 ${spacing.lg}`,
        backgroundColor: colors.navBackground,
        color: colors.navText,
        transition: "background-color 0.3s ease",
      }}
    >
      <Link
        to="/"
        style={{
          color: colors.navText,
          textDecoration: "none",
          fontSize: fontSizes.lg,
          fontWeight: fontWeights.bold,
          letterSpacing: "0.02em",
        }}
      >
        Official UK Voting Platform
      </Link>

      {/* Info icon button */}
      <div style={{ position: "relative" }}>
        <button
          onClick={() => setShowInfo(!showInfo)}
          aria-label="Information"
          style={{
            width: "32px",
            height: "32px",
            borderRadius: "50%",
            border: `2px solid ${colors.navText}`,
            backgroundColor: "transparent",
            color: colors.navText,
            fontSize: fontSizes.base,
            fontWeight: fontWeights.bold,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            lineHeight: 1,
          }}
        >
          i
        </button>

        {/* Info dropdown */}
        {showInfo && (
          <div
            style={{
              position: "absolute",
              top: "calc(100% + 8px)",
              right: 0,
              width: "240px",
              backgroundColor: colors.surface,
              color: colors.text.primary,
              border: `1px solid ${colors.border}`,
              borderRadius: theme.borderRadius.md,
              padding: spacing.md,
              boxShadow: colors.shadows.lg,
              fontSize: fontSizes.sm,
              zIndex: 200,
            }}
          >
            <p style={{ marginBottom: spacing.sm }}>
              The Official UK Voting Platform for secure online voting.
            </p>
            <button
              onClick={toggleTheme}
              style={{
                width: "100%",
                padding: `${spacing.xs} ${spacing.sm}`,
                backgroundColor: colors.surfaceAlt,
                border: `1px solid ${colors.border}`,
                borderRadius: theme.borderRadius.sm,
                color: colors.text.primary,
                fontSize: fontSizes.sm,
                cursor: "pointer",
              }}
            >
              {mode === "light" ? "🌙 Dark Mode" : "☀️ Light Mode"}
            </button>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;