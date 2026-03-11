// Voter registration page - Public page for voters to begin their voting registration

import React from "react";
import { useNavigate } from "react-router-dom";
import { useTheme } from "../../styles/ThemeContext";
import PrimaryButton from "../../components/PrimaryButton";
import {
  getPageTitleStyle,
  getFirstSectionStyle,
  getLinkStyle,
  getCardStyle,
  getCardTitleStyle,
  getCardTextStyle,
  getCardListStyle,
  getVoterPageContentWrapperStyle,
} from "../../styles/ui";

const VoterRegistrationPage: React.FC = () => {
  const { theme } = useTheme();
  const { colors, spacing } = theme;
  const navigate = useNavigate();
  const pageTitleStyle = getPageTitleStyle(theme);
  const firstSectionStyle = getFirstSectionStyle(theme);
  const linkStyle = getLinkStyle(theme);
  const cardStyle = getCardStyle(theme);
  const cardTitleStyle = getCardTitleStyle(theme);
  const cardTextStyle = getCardTextStyle(theme);
  const listStyle = getCardListStyle(theme);
  const wrapperStyle = getVoterPageContentWrapperStyle(theme);

  return (
    <div className="voter-registration-page">
      <style>{`
        .voter-registration-page a:hover { color: ${colors.primaryHover}; }
        .registration-cards-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: ${spacing.lg};
          margin-bottom: ${spacing.lg};
        }
        .registration-cards-grid-inner {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: ${spacing.xl};
        }
        @media (max-width: 768px) {
          .registration-cards-grid { grid-template-columns: 1fr; }
          .registration-cards-grid-inner { grid-template-columns: 1fr; }
        }
      `}</style>
      <div className="voter-registration-page voter-page-content" style={wrapperStyle}>
        <header>
          <h1 style={pageTitleStyle}>Register to Vote</h1>
        </header>

        {/* Register to vote intro */}
        <p style={firstSectionStyle}>
          You can use this service to get on the electoral register so you can vote in elections in the UK.
          <br /><br />
          You only need to register once - not for every election. If you have changed your name, address or nationality, you need to{" "}
          <a href="/voter/manage-registration" style={linkStyle}>update your registration details</a>.
          <br />
          To know more about the voting process, please visit the <a href="/voter/voting-process" style={linkStyle}>The Voting Process</a> page.
          <br /><br />
          This process will take around 5 minutes.
        </p>

        {/* Before you start + Who can register */}
        <div className="registration-cards-grid">
          <div style={cardStyle}>
            <h2 style={cardTitleStyle}>Before you start</h2>
            <p style={cardTextStyle}>
              You'll be asked for your National Insurance number (but you can still register if you do not have one).
            </p>
            <p style={{ ...cardTextStyle, marginBottom: 0 }}>
              <a href="https://www.gov.uk/find-national-insurance-number" style={linkStyle}>Find your National Insurance number here on Gov.UK</a>.
            </p>
            <br />
            <p style={cardTextStyle}>
              You will also be asked to register biometrics as part of the registration process.
            </p>
          </div>
          <div style={cardStyle}>
            <h2 style={cardTitleStyle}>Who can register to vote</h2>
            <p style={cardTextStyle}>
              You can register to vote up to 2 years before you reach voting age —{" "}
              <a href="/voter/voting-process" style={linkStyle}>check the rules around voting in the UK</a>.
              <br />
              <br />
              Please note, it is a criminal offence to register while pretending to be someone else.
            </p>
          </div>
        </div>

        {/* England/NI + Scotland/Wales */}
        <div className="registration-cards-grid">
          <div style={cardStyle}>
            <h2 style={cardTitleStyle}>If you live in England or Northern Ireland</h2>
            <p style={cardTextStyle}>You must be aged <strong>16 or over</strong> to register.</p>
            <p style={cardTextStyle}>You can register to vote if you're a British citizen or an Irish citizen.</p>
            <p style={cardTextStyle}>
              You can also register if you have permission (or do not need permission) to enter or stay in the UK, Channel Islands or Isle of Man and you're:
            </p>
            <ul style={listStyle}>
              <li>a Commonwealth citizen (including citizens of Cyprus and Malta)</li>
              <li>a citizen of Denmark, Luxembourg, Poland, Portugal or Spain</li>
              <li>a citizen of another EU country, who on or before 31 December 2020 had permission to enter or stay (or did not need permission) and this has continued without a break</li>
            </ul>
          </div>
          <div style={cardStyle}>
            <h2 style={cardTitleStyle}>If you live in Scotland or Wales</h2>
            <p style={cardTextStyle}>You must be aged <strong>14 or over</strong> to register.</p>
            <p style={cardTextStyle}>You can register to vote if you're a British citizen or an Irish citizen.</p>
            <p style={cardTextStyle}>
              You can also register if you have permission to enter or stay in the UK, Channel Islands or Isle of Man, or you do not need permission.
            </p>
          </div>
        </div>

        {/* If you live abroad */}
        <div style={{ ...cardStyle, marginBottom: spacing.lg }}>
          <h2 style={cardTitleStyle}>If you live abroad</h2>
          <div className="registration-cards-grid-inner">
            <div>
              <p style={cardTextStyle}>
                You can register as an overseas voter if you've previously lived in the UK and are either:
              </p>
              <ul style={listStyle}>
                <li>a British citizen</li>
                <li>an eligible Irish citizen registering to vote in Northern Ireland</li>
              </ul>
            </div>
            <div>
              <p style={cardTextStyle}>
                You'll need to give the postcode of the last UK address you were registered to vote at.
              </p>
              <p style={cardTextStyle}>
                If you've never registered to vote, you'll need to give the postcode of the last UK address you lived at.
              </p>
              <p style={{ ...cardTextStyle, marginBottom: 0 }}>You may also be asked for your passport details.</p>
            </div>
          </div>
        </div>

        <div style={{ textAlign: "center", marginTop: spacing.xl }}>
          <PrimaryButton onClick={() => navigate("/voter/registeration")}>Register to Vote</PrimaryButton>
        </div>
      </div>
    </div>
  );
};

export default VoterRegistrationPage;
