import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useTheme } from "../../styles/ThemeContext";
import {
  getLinkStyle,
  getRegistrationCardStyle,
  getRegistrationCardTitleStyle,
  getRegistrationCardTextStyle,
} from "../../styles/pageStyles";

const OfficialLandingPage: React.FC = () => {
  const { theme, mode, toggleTheme } = useTheme();
  const { colors, spacing, fontSizes, fontWeights, borderRadius } = theme;

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("")

  return (
    <div
      style={{
        position: "relative",
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: colors.background,
        padding: spacing.xl,
      }}
    >
      {/* Theme toggle - top right corner */}
      <button
        type="button"
        onClick={toggleTheme}
        aria-label="Toggle theme"
        title={mode === "light" ? "Switch to Dark Mode" : "Switch to Light Mode"}
        style={{
          position: "absolute",
          top: spacing.md,
          right: spacing.md,
          padding: spacing.sm,
          backgroundColor: colors.surfaceAlt,
          border: `1px solid ${colors.border}`,
          borderRadius: borderRadius.md,
          color: colors.text.primary,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: colors.shadows.sm,
        }}
      >
        {mode === "light" ? (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={colors.text.primary} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z" />
          </svg>
        ) : (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={colors.text.primary} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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

      <div
        style={{
          ...getRegistrationCardStyle(theme),
          maxWidth: "420px",
          width: "100%",
        }}
      >
        <h1
          style={{
            ...getRegistrationCardTitleStyle(theme),
            marginTop: 0,
            marginBottom: spacing.xl,
            textAlign: "center",
            textTransform: "uppercase",
            letterSpacing: "0.02em",
            color: colors.text.primary,
          }}
        >
          Election Official Login
        </h1>

        <form>
          <div style={{ marginBottom: spacing.lg }}>
            <label
              htmlFor="username"
              style={{
                display: "block",
                marginBottom: spacing.xs,
                fontSize: fontSizes.base,
                fontWeight: fontWeights.normal,
                color: colors.text.primary,
              }}
            >
              Username:
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              style={{
                width: "100%",
                padding: `${spacing.sm} ${spacing.md}`,
                fontSize: fontSizes.base,
                border: `1px solid ${colors.border}`,
                borderRadius: borderRadius.sm,
                backgroundColor: colors.surface,
                color: colors.text.primary,
                boxSizing: "border-box",
              }}
            />
          </div>

          <div style={{ marginBottom: spacing.xl }}>
            <label
              htmlFor="password"
              style={{
                display: "block",
                marginBottom: spacing.xs,
                fontSize: fontSizes.base,
                fontWeight: fontWeights.normal,
                color: colors.text.primary,
              }}
            >
              Password:
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: "100%",
                padding: `${spacing.sm} ${spacing.md}`,
                fontSize: fontSizes.base,
                border: `1px solid ${colors.border}`,
                borderRadius: borderRadius.sm,
                backgroundColor: colors.surface,
                color: colors.text.primary,
                boxSizing: "border-box",
              }}
            />
          </div>

          <button
            type="submit"
            style={{
              width: "100%",
              padding: `${spacing.md} ${spacing.lg}`,
              fontSize: fontSizes.base,
              fontWeight: fontWeights.medium,
              color: colors.text.inverse,
              backgroundColor: colors.button,
              border: "none",
              borderRadius: borderRadius.md,
              cursor: "pointer",
            }}
          >
            Login
          </button>
        </form>

        <p
          style={{
            marginTop: spacing.lg,
            marginBottom: spacing.xs,
            fontSize: fontSizes.sm,
            textAlign: "center",
          }}
        >
          <Link to="/official/forgot-password" style={getLinkStyle(theme)}>
            Forgot password?
          </Link>
        </p>
        <p
          style={{
            ...getRegistrationCardTextStyle(theme),
            margin: 0,
            textAlign: "center",
            fontStyle: "italic",
            fontSize: fontSizes.sm,
          }}
        >
          If you have any queries or have forgotten your password, please contact admin@UKElection.com
        </p>
      </div>
    </div>
  );
};

export default OfficialLandingPage;
