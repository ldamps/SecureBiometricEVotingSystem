/**
 * Chromeless layout for the authenticator PWA.
 * No navigation bar — just a compact app header and the page content.
 */

import { Outlet } from "react-router-dom";
import { useTheme } from "../styles/ThemeContext";

function AuthenticatorLayout() {
  const { theme } = useTheme();

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        backgroundColor: theme.colors.background,
        color: theme.colors.text.primary,
      }}
    >
      {/* Compact header */}
      <header
        style={{
          padding: "0.75rem 1rem",
          backgroundColor: theme.colors.primary,
          color: theme.colors.text.inverse,
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
        }}
      >
        <img
          src="/electionLogo.svg"
          alt=""
          style={{ width: "28px", height: "28px" }}
        />
        <span style={{ fontSize: "1.1rem", fontWeight: 600 }}>
          E-Voting Authenticator
        </span>
      </header>

      <main style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <Outlet />
      </main>
    </div>
  );
}

export default AuthenticatorLayout;
