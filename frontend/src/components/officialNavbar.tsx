import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTheme } from "../styles/ThemeContext";
import { SecondaryButton } from "../styles/ui";
import { clearAuthSession, getAccessTokenSubject } from "../services/api-client.service";
import { OfficialApiRepository } from "../features/officials/repositories/official-api.repository";
import { OfficialRole } from "../features/officials/model/official.model";

const officialApiRepository = new OfficialApiRepository();

const OfficialNavbar: React.FC = () => {
  const { theme, mode, toggleTheme } = useTheme();
  const { colors, spacing, fontWeights } = theme;
  const navigate = useNavigate();

  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const officialId = getAccessTokenSubject();
    if (!officialId) return;
    officialApiRepository.getOfficial(officialId)
      .then((official) => setIsAdmin(official.role === OfficialRole.ADMIN))
      .catch(() => setIsAdmin(false));
  }, []);

  const handleLogout = () => {
    clearAuthSession();
    navigate("/official/landing");
  };

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

      {/* Right side: admin links, logout, profile, theme toggle */}
      <div style={{ display: "flex", alignItems: "center", gap: spacing.md }}>

        {isAdmin && (
          <>
            <Link
              to="/official/elections"
              style={{
                color: colors.navText,
                textDecoration: "none",
                fontSize: theme.fontSizes.sm,
                fontWeight: fontWeights.medium,
                opacity: 0.9,
              }}
            >
              Elections
            </Link>
            <Link
              to="/official/referendums"
              style={{
                color: colors.navText,
                textDecoration: "none",
                fontSize: theme.fontSizes.sm,
                fontWeight: fontWeights.medium,
                opacity: 0.9,
              }}
            >
              Referendums
            </Link>
            <Link
              to="/official/officials"
              style={{
                color: colors.navText,
                textDecoration: "none",
                fontSize: theme.fontSizes.sm,
                fontWeight: fontWeights.medium,
                opacity: 0.9,
              }}
            >
              Officials
            </Link>
          </>
        )}

        <SecondaryButton onClick={handleLogout}>Logout</SecondaryButton>

        <Link
          to="/official/profile"
          style={{ display: "flex", alignItems: "center", textDecoration: "none" }}
        >
          <button
            type="button"
            aria-label="Profile"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 40,
              height: 40,
              padding: 0,
              margin: 0,
              backgroundColor: "transparent",
              border: "none",
              color: colors.navText,
              cursor: "pointer",
            }}
          >
            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke={colors.navText} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" />
              <path d="M12 10m-3 0a3 3 0 1 0 6 0a3 3 0 1 0 -6 0" />
              <path d="M6.168 18.849a4 4 0 0 1 3.832 -2.849h2.332a4 4 0 0 1 3.832 2.849" />
            </svg>
          </button>
        </Link>

        {/* Light/Dark mode toggle */}
        <button
          type="button"
          onClick={toggleTheme}
          aria-label="Toggle theme"
          title={mode === "light" ? "Switch to Dark Mode" : "Switch to Light Mode"}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: 40,
            height: 40,
            padding: 0,
            margin: 0,
            backgroundColor: "transparent",
            border: "none",
            color: colors.navText,
            cursor: "pointer",
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