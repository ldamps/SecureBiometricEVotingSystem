// Voter registration page - Public page for voters to begin their voting registration

import React from "react";
import { useNavigate } from "react-router-dom";
import { useTheme } from "../../styles/ThemeContext";
import PrimaryButton from "../../components/PrimaryButton";
import {
  VoterPageWrapper,
  VoterPageHeader,
  VoterFirstSection,
  VoterCard,
  VoterLink,
  getRegistrationCardTextStyle,
  getRegistrationListStyle,
} from "../../features/voter/components";

const VoterRegistrationPage: React.FC = () => {
  const { theme } = useTheme();
  const { colors, spacing } = theme;
  const navigate = useNavigate();
  const cardTextStyle = getRegistrationCardTextStyle(theme);
  const listStyle = getRegistrationListStyle(theme);

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
          .registration-cards-grid {
            grid-template-columns: 1fr;
          }
          .registration-cards-grid-inner {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
      <VoterPageWrapper className="voter-registration-page">
        <VoterPageHeader title="Register to Vote" />

        {/* Register to vote intro */}
        <VoterFirstSection>
          You can use this service to get on the electoral register so you can vote in elections in the UK.
          <br />
          <br />
          You only need to register once - not for every election. If you have changed your name, address or nationality, you need to{" "}
          <VoterLink href="/voter/manage-registration">update your registration details</VoterLink>.
          <br />
          To know more about the voting process, please visit the <VoterLink href="/voter/voting-process">The Voting Process</VoterLink> page.
          <br />
          <br />
          This process will take around 5 minutes.
        </VoterFirstSection>

        {/* Before you start + Who can register - side by side (stack on mobile) */}
        <div className="registration-cards-grid">
          {/* Before you start */}
          <VoterCard title="Before you start">
            <p style={cardTextStyle}>
              You'll be asked for your National Insurance number (but you can still register if you do not have one).
            </p>
            <p style={{ ...cardTextStyle, marginBottom: 0 }}>
              <VoterLink href="https://www.gov.uk/find-national-insurance-number">Find your National Insurance number here on Gov.UK</VoterLink>.
            </p>
            <br />
            <p style={cardTextStyle}>
                You will also be asked to register biometrics as part of the registration process.
            </p>
          </VoterCard>

          {/* Who can register */}
          <VoterCard title="Who can register to vote">
            <p style={cardTextStyle}>
              You can register to vote up to 2 years before you reach voting age —{" "}
              <VoterLink href="/voter/voting-process">check the rules around voting in the UK</VoterLink>.
            </p>
          </VoterCard>
        </div>

        {/* England/NI + Scotland/Wales - side by side (stack on mobile) */}
        <div className="registration-cards-grid">
          {/* England or Northern Ireland */}
          <VoterCard title="If you live in England or Northern Ireland">
            <p style={cardTextStyle}>
              You must be aged <strong>16 or over</strong> to register.
            </p>
            <p style={cardTextStyle}>
              You can register to vote if you're a British citizen or an Irish citizen.
            </p>
            <p style={cardTextStyle}>
              You can also register if you have permission (or do not need permission) to enter or stay in the UK, Channel Islands or Isle of Man and you're:
            </p>
            <ul style={listStyle}>
              <li>a Commonwealth citizen (including citizens of Cyprus and Malta)</li>
              <li>a citizen of Denmark, Luxembourg, Poland, Portugal or Spain</li>
              <li>a citizen of another EU country, who on or before 31 December 2020 had permission to enter or stay (or did not need permission) and this has continued without a break</li>
            </ul>
          </VoterCard>

          {/* Scotland or Wales */}
          <VoterCard title="If you live in Scotland or Wales">
            <p style={cardTextStyle}>
              You must be aged <strong>14 or over</strong> to register.
            </p>
            <p style={cardTextStyle}>
              You can register to vote if you're a British citizen or an Irish citizen.
            </p>
            <p style={cardTextStyle}>
              You can also register if you have permission to enter or stay in the UK, Channel Islands or Isle of Man, or you do not need permission.
            </p>
          </VoterCard>
        </div>

        {/* If you live abroad - full width (inner columns stack on mobile) */}
        <VoterCard title="If you live abroad" style={{ marginBottom: spacing.lg }}>
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
            <p style={{ ...cardTextStyle}}>
                You'll need to give the postcode of the last UK address you were registered to vote at.
              </p>
              <p style={cardTextStyle}>
                If you've never registered to vote, you'll need to give the postcode of the last UK address you lived at.
              </p>
              <p style={{ ...cardTextStyle, marginBottom: 0 }}>
                You may also be asked for your passport details.
              </p>
            </div>
          </div>
        </VoterCard>
        { /* Register to vote button */}
        <div style={{ textAlign: "center", marginTop: spacing.xl }}>
          <PrimaryButton onClick={() => navigate("/voter/register")}>Register to Vote</PrimaryButton>
        </div>
      </VoterPageWrapper>
    </div>
  );
};

export default VoterRegistrationPage;