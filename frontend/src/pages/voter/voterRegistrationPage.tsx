
import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTheme } from "../../styles/ThemeContext";

const VoterRegistrationPage: React.FC = () => {
    const { theme } = useTheme();
    const { colors, spacing, fontSizes, fontWeights, fonts, layout } = theme;
    const navigate = useNavigate();

    return (
        <div>
            <header>
                <h1
                    style={{
                    fontSize: fontSizes["3xl"],
                    fontWeight: fontWeights.bold,
                    color: colors.text.primary,
                    marginBottom: spacing.sm,
                    lineHeight: 1.2,
                    padding: spacing.xl,
                    }}
                >
                    Register to Vote
                </h1>
            </header>
        </div>
    )
}

export default VoterRegistrationPage;
