// Voter manage registration voting details - Public page for voters to begin updating their voting details

import React from "react";
import { useTheme } from "../../styles/ThemeContext";
import { PrimaryButton } from "../../styles/ui";
import { useNavigate } from "react-router-dom";
import {
  getListStyle,
  getPageTitleStyle,
  getFirstSectionStyle,
  getLinkStyle,
  getVoterPageContentWrapperStyle,
} from "../../styles/ui";

const VoterManageRegistrationPage: React.FC = () => {
  const { theme } = useTheme();
  const { spacing } = theme;
  const listStyle = getListStyle(theme);
  const pageTitleStyle = getPageTitleStyle(theme);
  const firstSectionStyle = getFirstSectionStyle(theme);
  const linkStyle = getLinkStyle(theme);
  const wrapperStyle = getVoterPageContentWrapperStyle(theme);
  const navigate = useNavigate();

  return (
    <div className="voter-manage-registration-page">
      <div className="voter-manage-registration-page voter-page-content" style={wrapperStyle}>
        <header>
          <h1 style={pageTitleStyle}>Manage your voting details</h1>
        </header>

        {/* Manage voting details intro */}
        <div style={firstSectionStyle}>
          You can use this service to update your voting details, including:
          <ul style={listStyle}>
            <li>Your legal name</li>
            <li>Your current address</li>
            <li>Your email address</li>
            <li>Renewing your biometric details</li>
            <li>Your nationality (if you live in the UK)</li>
          </ul>
          If you have not registered to vote yet, you can <a href="/voter/register" style={linkStyle}>register to vote here</a>.
        </div>

        {/* Manage voting details button */}
        <div style={{ textAlign: "left", marginTop: spacing.xl, marginLeft: spacing.xl }}>
          <PrimaryButton onClick={() => navigate("/voter/update-registration")}>Update your registration details</PrimaryButton>
        </div>
      </div>
    </div>
  );
};

export default VoterManageRegistrationPage;
