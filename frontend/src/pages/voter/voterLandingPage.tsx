// Voter landing page - Public page for voters

import React from "react";
import { useNavigate } from "react-router-dom";
import { useTheme } from "../../styles/ThemeContext";
import { getVoterPageContentWrapperStyle } from "../../styles/pageStyles";

const VoterLandingPage: React.FC = () => {
  const { theme } = useTheme();
  const { colors, spacing, fontSizes, fontWeights, fonts, layout } = theme;
  const navigate = useNavigate();
  const wrapperStyle = getVoterPageContentWrapperStyle(theme);

  return (
    <div
      style={{
        height: `calc(100vh - ${layout.navHeight})`,
        backgroundColor: colors.background,
        fontFamily: fonts.body,
        display: "flex",
        flexDirection: "column",
        padding: spacing["2xl"],
      }}
    >
      <div className="container voter-page-content" style={{ ...wrapperStyle, flex: 1, display: "flex", flexDirection: "column" }}>
        {/* Welcome header */}
        <header style={{ marginBottom: spacing.xl, textAlign: "center" }}>
          <h1
            style={{
              fontSize: fontSizes["4xl"],
              fontWeight: fontWeights.bold,
              color: colors.text.primary,
              marginBottom: spacing.sm,
              lineHeight: 1.2,
            }}
          >
            Welcome to the Official UK Voting Platform
          </h1>
          <p
            style={{
              fontSize: fontSizes.lg,
              color: colors.text.secondary,
              margin: 0,
              lineHeight: 1.6,
            }}
          >
            Select an option below to get started
          </p>
        </header>

        {/* Grid area fills remaining space */}
        <div
          style={{
            flex: 1,
            display: "grid",
            gridTemplateColumns: "1.2fr 1fr",
            gridTemplateRows: "1fr 1fr",
            gap: spacing.lg,
            minHeight: 0,
          }}
        >
        {/* Vote - spans both rows on the left */}
        <button
          className="button-base"
          style={{
            gridRow: "1 / 3",
            fontSize: fontSizes["4xl"],
            fontWeight: fontWeights.bold,
            letterSpacing: "0.04em",
          }}
        >
          Vote
        </button>

        {/* Register To Vote - top right */}
        <button
          className="button-base"
          style={{
            fontSize: fontSizes["2xl"],
            fontWeight: fontWeights.semibold,
          }}
          onClick={() => navigate("/voter/register")}
        >
          Register To Vote
        </button>

        {/* Manage Vote Registration Details - bottom right */}
        <button
          className="button-base"
          style={{
            fontSize: fontSizes["2xl"],
            fontWeight: fontWeights.semibold,
            padding: spacing.lg,
          }}
          onClick={() => navigate("/voter/manage-registration")}
        >
          Manage Vote
          <br />
          Registration Details
        </button>
        </div>
      </div>
    </div>
  );
};

export default VoterLandingPage;

