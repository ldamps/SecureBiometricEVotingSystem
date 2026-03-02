// Voter manage registration voting details - Public page for voters to begin updating their voting details

import React from "react";
import { useTheme } from "../../styles/ThemeContext";
import { getFirstSectionStyle, getLinkStyle, getListStyle, getPageTitleStyle, getVoterPageContentWrapperStyle } from "../../styles/pageStyles";
import PrimaryButton from "../../components/PrimaryButton";
import { useNavigate } from "react-router-dom";

const VoterManageRegistrationPage: React.FC = () => {
    const { theme } = useTheme();
    const { spacing } = theme;
    const wrapperStyle = getVoterPageContentWrapperStyle(theme);
    const pageTitleStyle = getPageTitleStyle(theme);
    const firstSectionStyle = getFirstSectionStyle(theme);
    const listStyle = getListStyle(theme);
    const linkStyle = getLinkStyle(theme);
    const navigate = useNavigate();
    
    return (
        <div className="voter-manage-registration-page">
            <div className="voter-manage-registration-page voter-page-content" style={{ ...wrapperStyle }}>
                <header>
                    <h1 style={pageTitleStyle}>Manage your voting details</h1>
                </header>

                { /* Manage voting details intro */}
                <p style={firstSectionStyle}>
                    You can use this service to update your voting details, including:
                    <ul style={listStyle}>
                    <li>Your legal name</li>
                    <li>Your current address</li>
                    <li>Your email address</li>
                    <li>Renewing your biometric details</li>
                    <li>Your nationality (if you live in the UK)</li>
                    <li>Your occupation (if you are a crown servant, British Council employee or member of the armed forces)</li>
                </ul>
                If you have not registered to vote yet, you can <a style={linkStyle} href="/voter/register">register to vote here</a>.
                </p>

                { /* Manage voting details button */}
                <div style={{ textAlign: "left", marginTop: spacing.xl, marginLeft: spacing.xl }}>
                    <PrimaryButton onClick={() => navigate("/voter/manage-registration")}>Update your registration details</PrimaryButton>
                </div>
                
            </div>
        </div>
    )
};

export default VoterManageRegistrationPage;