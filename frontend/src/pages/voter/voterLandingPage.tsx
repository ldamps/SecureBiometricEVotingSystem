
import React from "react";
import { useNavigate } from "react-router-dom";
import { useTheme } from "../../styles/ThemeContext";

const VoterLandingPage: React.FC = () => {
    const { theme } = useTheme();
    const { colors, spacing, fontSizes, fontWeights, layout } = theme;

    return (
        <div style={{ padding: `${spacing.xl} ${spacing.md}` }}>
            <h1 style={{ fontSize: fontSizes.xl, fontWeight: fontWeights.bold }}>Welcome to the Voter Landing Page</h1>
        </div>
    );
};

export default VoterLandingPage;

