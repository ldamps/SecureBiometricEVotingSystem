// Navbar component for the e-voting platform - will be seen on all pages



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
        zIndex: 200,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        height: "72px",
        padding: `0 ${spacing.lg}`,
        backgroundColor: colors.navBackground,
        color: colors.navText,
        transition: "background-color 0.3s ease",
      }}
    >
      <Link
        to="/voter/landing"
        style={{
          color: colors.navText,
          textDecoration: "none",
          fontSize: fontSizes["2xl"],
          fontWeight: fontWeights.bold,
          letterSpacing: "0.02em",
        }}
      >
        Official UK Voting Platform
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

        {/* Info icon button */}
        <div style={{ position: "relative" }}>
          <button
            onClick={() => setShowInfo(!showInfo)}
            aria-label="Information"
            title="Information"
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "50%",
              border: `2px solid ${colors.navText}`,
              backgroundColor: "transparent",
              color: colors.navText,
              fontSize: fontSizes.lg || "1.125rem",
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

          {/* Info dropdown with options */}
          {showInfo && (
            <div
              style={{
                position: "absolute",
                top: "calc(100% + 8px)",
                right: 0,
                width: "260px",
                backgroundColor: colors.surface,
                color: colors.text.primary,
                border: `1px solid ${colors.border}`,
                borderRadius: theme.borderRadius.md,
                padding: spacing.md,
                boxShadow: colors.shadows.lg,
                fontSize: fontSizes.base || "1rem",
                zIndex: 200,
              }}
            >
              <p style={{ marginBottom: spacing.md, fontSize: fontSizes.base || "1rem" }}>
                The Official UK Voting Platform for secure online voting.
              </p>
              <nav
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: spacing.xs,
                }}
              >
                <Link
                  to="/voter/about"
                  onClick={() => setShowInfo(false)}
                  style={{
                    display: "block",
                    padding: `${spacing.xs} ${spacing.sm}`,
                    backgroundColor: colors.surfaceAlt,
                    border: `1px solid ${colors.border}`,
                    borderRadius: theme.borderRadius.sm,
                    color: colors.text.primary,
                    fontSize: fontSizes.base || "1rem",
                    textDecoration: "none",
                    textAlign: "center",
                    cursor: "pointer",
                  }}
                >
                  About the Platform
                </Link>
                <Link
                  to="/voter/voting-process"
                  onClick={() => setShowInfo(false)}
                  style={{
                    display: "block",
                    padding: `${spacing.xs} ${spacing.sm}`,
                    backgroundColor: colors.surfaceAlt,
                    border: `1px solid ${colors.border}`,
                    borderRadius: theme.borderRadius.sm,
                    color: colors.text.primary,
                    fontSize: fontSizes.base || "1rem",
                    textDecoration: "none",
                    textAlign: "center",
                    cursor: "pointer",
                  }}
                >
                  The Voting Process
                </Link>
                <Link
                  to="/voter/register"
                  onClick={() => setShowInfo(false)}
                  style={{
                    display: "block",
                    padding: `${spacing.xs} ${spacing.sm}`,
                    backgroundColor: colors.surfaceAlt,
                    border: `1px solid ${colors.border}`,
                    borderRadius: theme.borderRadius.sm,
                    color: colors.text.primary,
                    fontSize: fontSizes.base || "1rem",
                    textDecoration: "none",
                    textAlign: "center",
                    cursor: "pointer",
                  }}
                >
                  Register to Vote
                </Link>
                <Link
                  to="/voter/register"
                  onClick={() => setShowInfo(false)}
                  style={{
                    display: "block",
                    padding: `${spacing.xs} ${spacing.sm}`,
                    backgroundColor: colors.surfaceAlt,
                    border: `1px solid ${colors.border}`,
                    borderRadius: theme.borderRadius.sm,
                    color: colors.text.primary,
                    fontSize: fontSizes.base || "1rem",
                    textDecoration: "none",
                    textAlign: "center",
                    cursor: "pointer",
                  }}
                >
                  Manage Vote Registration
                </Link>
                <Link
                  to="/"
                  onClick={() => setShowInfo(false)}
                  style={{
                    display: "block",
                    padding: `${spacing.xs} ${spacing.sm}`,
                    backgroundColor: colors.surfaceAlt,
                    border: `1px solid ${colors.border}`,
                    borderRadius: theme.borderRadius.sm,
                    color: colors.text.primary,
                    fontSize: fontSizes.base || "1rem",
                    textDecoration: "none",
                    textAlign: "center",
                    cursor: "pointer",
                  }}
                >
                  Vote Now
                </Link>
              </nav>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;