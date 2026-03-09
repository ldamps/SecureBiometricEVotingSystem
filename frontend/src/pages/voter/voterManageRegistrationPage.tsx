// Voter manage registration voting details - Public page for voters to begin updating their voting details

import React from "react";
import { useTheme } from "../../styles/ThemeContext";
import PrimaryButton from "../../components/PrimaryButton";
import { useNavigate } from "react-router-dom";
import { VoterPageWrapper, VoterPageHeader, VoterFirstSection, VoterLink, getListStyle } from "../../features/voter/components";

const VoterManageRegistrationPage: React.FC = () => {
    const { theme } = useTheme();
    const { spacing } = theme;
    const listStyle = getListStyle(theme);
    const navigate = useNavigate();

    return (
        <div className="voter-manage-registration-page">
            <VoterPageWrapper className="voter-manage-registration-page">
                <VoterPageHeader title="Manage your voting details" />

                { /* Manage voting details intro */}
                <VoterFirstSection as="div">
                    You can use this service to update your voting details, including:
                    <ul style={listStyle}>
                        <li>Your legal name</li>
                        <li>Your current address</li>
                        <li>Your email address</li>
                        <li>Renewing your biometric details</li>
                        <li>Your nationality (if you live in the UK)</li>
                        <li>Your occupation (if you are a crown servant, British Council employee or member of the armed forces)</li>
                    </ul>
                    If you have not registered to vote yet, you can <VoterLink href="/voter/register">register to vote here</VoterLink>.
                </VoterFirstSection>

                { /* Manage voting details button */}
                <div style={{ textAlign: "left", marginTop: spacing.xl, marginLeft: spacing.xl }}>
                    <PrimaryButton onClick={() => navigate("/voter/manage-registration")}>Update your registration details</PrimaryButton>
                </div>
            </VoterPageWrapper>
        </div>
    )
};

export default VoterManageRegistrationPage;