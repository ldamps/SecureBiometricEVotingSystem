import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTheme } from "../../styles/ThemeContext";

const VoterVotingProcessPage: React.FC = () => {
    const { theme } = useTheme();
    const { colors, spacing, fontSizes, fontWeights, fonts, layout } = theme;
    const navigate = useNavigate();

    return (
        <div>
            <h1>The Voting Process</h1>
        </div>
    )
}

export default VoterVotingProcessPage;