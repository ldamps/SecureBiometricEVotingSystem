// Voting page - Voter voting page

import React from "react";
import { useTheme } from "../../styles/ThemeContext";
import { getFirstSectionStyle, getLinkStyle, getListStyle, getPageTitleStyle } from "../../styles/pageStyles";
import PrimaryButton from "../../components/PrimaryButton";
import { useNavigate } from "react-router-dom";

const VoteCastingPage: React.FC = () => {
    const { theme } = useTheme();
    const { spacing } = theme;
    const navigate = useNavigate();
    const pageTitleStyle = getPageTitleStyle(theme);
    const firstSectionStyle = getFirstSectionStyle(theme);
    const listStyle = getListStyle(theme);
    const linkStyle = getLinkStyle(theme);

    return (
        <div className="voter-voting-page">
            <header>
                <h1 style={pageTitleStyle}>Vote</h1>
            </header>
            <p style={firstSectionStyle}>
                You can use this service to cast your vote in the UK.
                <br />
                The voting process will take around 5 minutes. You will be asked to:
                <ul style={listStyle}>
                    <li>Select the election you want to vote in</li>
                    <li>Enter your registration details to confirm your identity</li>
                    <li>Biometrically verify your identity</li>
                    <li>Cast your vote</li>
                </ul>
                All votes are recorded anonymously and securely.
                To know more about the voting process, please visit the <a style={linkStyle} href="/voter/voting-process">The Voting Process</a> page.
                <br />
                <br />
                <p>
                    <i>Please note:
                        <ul style={listStyle}>
                            <li>You must be registered and eligible to vote in order to cast your vote. 
                            <br />
                            If you have not registered to vote yet, you can <a style={linkStyle} href="/voter/register">register to vote here</a></li>
                            <li>Your registrations need to be up-to-date. <br /> 
                            If you have changed your name, address or nationality, you need to <a style={linkStyle} href="/voter/manage-registration">update your registration details</a></li>
                            <li>You can only vote once.</li>
                            <li>You are only eligible to vote in elections run in your current constituency.</li>
                            <li>Once verified, you will have 10 minutes to cast your vote. If you do not cast your vote within 10 minutes, you will need to start the process again.</li>
                        </ul>
                    </i>
                </p>
                <PrimaryButton onClick={() => navigate("/voter/landing")}>Vote</PrimaryButton>
            </p>
        </div>
    )
};

export default VoteCastingPage;