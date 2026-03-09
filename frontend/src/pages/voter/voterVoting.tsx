// Voting page - Voter voting page

import React from "react";
import { useTheme } from "../../styles/ThemeContext";
import PrimaryButton from "../../components/PrimaryButton";
import { useNavigate } from "react-router-dom";
import {
  getPageTitleStyle,
  getFirstSectionStyle,
  getListStyle,
  getLinkStyle,
  getCardStyle,
  getCardTitleStyle,
  getCardTextStyle,
  getCardListStyle,
  getVoterPageContentWrapperStyle,
} from "../../styles/ui";

const VoteCastingPage: React.FC = () => {
  const { theme } = useTheme();
  const navigate = useNavigate();
  const pageTitleStyle = getPageTitleStyle(theme);
  const firstSectionStyle = getFirstSectionStyle(theme);
  const listStyle = getListStyle(theme);
  const linkStyle = getLinkStyle(theme);
  const cardStyle = getCardStyle(theme);
  const cardTitleStyle = getCardTitleStyle(theme);
  const cardTextStyle = getCardTextStyle(theme);
  const cardListStyle = getCardListStyle(theme);
  const wrapperStyle = getVoterPageContentWrapperStyle(theme);

  return (
    <div className="voter-voting-page">
      <div className="voter-voting-page voter-page-content" style={wrapperStyle}>
        <header>
          <h1 style={pageTitleStyle}>Vote</h1>
        </header>
        <div style={firstSectionStyle}>
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
          To know more about the voting process, please visit the <a href="/voter/voting-process" style={linkStyle}>The Voting Process</a> page.
          <br /><br />
          <div style={cardStyle}>
            <h2 style={cardTitleStyle}>Please note</h2>
            <ul style={cardListStyle}>
              <li style={cardTextStyle}>
                You must be registered and eligible to vote in order to cast your vote.
                <br />
                If you have not registered to vote yet, you can <a href="/voter/register" style={linkStyle}>register to vote here</a>.
              </li>
              <li style={cardTextStyle}>
                Your registrations need to be up-to-date.
                <br />
                If you have changed your name, address or nationality, you need to <a href="/voter/manage-registration" style={linkStyle}>update your registration details</a>.
              </li>
              <li style={cardTextStyle}>
                You can only vote once.
                <br />
                You are only eligible to vote in elections run in your current constituency.
              </li>
              <li style={cardTextStyle}>You are only eligible to vote in elections run in your current constituency.</li>
              <li style={cardTextStyle}>Once verified, you will have 10 minutes to cast your vote. If you do not cast your vote within 10 minutes, you will need to start the process again.</li>
            </ul>
          </div>
          <br />
          <PrimaryButton onClick={() => navigate("/voter/landing")}>Vote</PrimaryButton>
        </div>
      </div>
    </div>
  );
};

export default VoteCastingPage;
