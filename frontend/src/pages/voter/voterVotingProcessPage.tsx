import React from "react";
import { useTheme } from "../../styles/ThemeContext";
import { getFirstSectionStyle, getH3Style, getLinkStyle, getListStyle, getPageTitleStyle, getPAfterHeaderStyle, getSectionH2Style, getSectionIconStyle, getSectionWithPaddingStyle, getVoterPageContentWrapperStyle } from "../../styles/ui";

const VoterVotingProcessPage: React.FC = () => {
  const { theme } = useTheme();
  const pageTitleStyle = getPageTitleStyle(theme);
  const wrapperStyle = getVoterPageContentWrapperStyle(theme);
  const firstSectionStyle = getFirstSectionStyle(theme);
  const sectionH2Style = getSectionH2Style(theme);
  const sectionWithPaddingStyle = getSectionWithPaddingStyle(theme);
  const h3Style = getH3Style(theme);
  const pAfterHeaderStyle = getPAfterHeaderStyle(theme);
  const listStyle = getListStyle(theme);
  const linkStyle = getLinkStyle(theme);
  const sectionIconStyle = getSectionIconStyle(theme);

  const sectionDiamond = (
    <svg width="0.65em" height="0.65em" viewBox="0 0 24 24" style={sectionIconStyle} aria-hidden>
      <rect x="4" y="4" width="16" height="16" rx="2" transform="rotate(45 12 12)" />
    </svg>
  );

  return (
    <div className="voter-voting-process-page">
      <style>{`
        .voter-voting-process-page a:hover { color: ${theme.colors.primaryHover}; }
      `}</style>
      <div className="voter-voting-process-page voter-page-content" style={wrapperStyle}>
        <header>
          <h1 style={pageTitleStyle}>The Voting Process</h1>
        </header>
        <p style={firstSectionStyle}>
          The Official UK Voting Platform allows you to cast your vote entirely online. The platform supports elections and referendums across a range of UK democratic processes, including General Elections, Local Elections, Mayoral Elections, and devolved assembly elections. Your identity is verified through biometric authentication, and your vote is kept completely anonymous through a secure ballot token system.
        </p>

        {/* Before You Vote */}
        <section style={sectionWithPaddingStyle}>
          <h2 style={sectionH2Style}>Before You Vote</h2>
          <p style={pAfterHeaderStyle}>
            In order to vote, you must first be registered on this platform. You can register at the <a href="/voter/register" style={linkStyle}>Register to Vote</a> page.
            <br />
            <br />
            As part of registration, you will need to provide your personal details and set up biometric authentication on your device. This involves enrolling your facial and ear biometrics, which generates a secure cryptographic key stored on your device. Your raw biometric data is never sent to our servers.
            <br />
            <br />
            Before you vote, please ensure your registration details are up to date. You may update your details at any time on the <a href="/voter/manage-registration" style={linkStyle}>manage your voting details</a> page.
          </p>
        </section>

        {/* The Step-by-Step Voting Process */}
        <section style={sectionWithPaddingStyle}>
          <h2 style={sectionH2Style}>The Step-by-Step Voting Process</h2>
          <p style={pAfterHeaderStyle}>
            The voting process takes around 5 to 10 minutes. You can begin from the <a href="/voter/voting" style={linkStyle}>Begin Vote</a> page.
          </p>

          {/* Step 1: Select an Election or Referendum */}
          <h3 style={h3Style}>{sectionDiamond}Step 1: Select an Election or Referendum</h3>
          <p style={pAfterHeaderStyle}>
            You will be presented with a list of elections and referendums that are currently open for voting. Select the one you wish to participate in and press "Next" to continue.
          </p>

          {/* Step 2: Confirm Your Identity */}
          <h3 style={h3Style}>{sectionDiamond}Step 2: Confirm Your Identity</h3>
          <p style={pAfterHeaderStyle}>
            You will be asked to confirm your identity by providing the following details:
            <ul style={listStyle}>
              <li>Full Name</li>
              <li>Address Line 1</li>
              <li>Address Line 2</li>
              <li>City / Town</li>
              <li>Postcode</li>
            </ul>
            These details will be checked against the electoral roll. You will be unable to proceed if:
            <ul style={listStyle}>
              <li>Your name is not found on the electoral roll</li>
              <li>Your address is outside the constituency for your selected election</li>
              <li>Your name and address do not match the electoral roll records</li>
            </ul>
          </p>

          {/* Step 3: Biometric Verification */}
          <h3 style={h3Style}>{sectionDiamond}Step 3: Biometric Verification</h3>
          <p style={pAfterHeaderStyle}>
            Once your identity has been confirmed on the electoral roll, you will be asked to verify your identity using biometric authentication. This uses both facial and ear recognition to ensure that you are who you say you are, reducing the risk of electoral fraud.
            <br />
            <br />
            The verification works through a secure challenge-response process. The server sends a cryptographic challenge to your device, which can only be answered by unlocking your private key with a successful biometric match. Both facial and ear biometrics must pass independently. Your raw biometric data never leaves your device during this process.
            <br />
            <br />
            You will be given 3 attempts to verify your identity. If all attempts fail, your account will be temporarily locked. Once verified, press "Next" to continue.
          </p>

          {/* Step 4: Ballot Token and Candidate Selection */}
          <h3 style={h3Style}>{sectionDiamond}Step 4: Candidate Selection</h3>
          <p style={pAfterHeaderStyle}>
            After biometric verification, you will receive a one-time ballot token. This token allows you to cast your vote anonymously — it cannot be traced back to your identity.
            <br />
            <br />
            Once you enter this stage, a 10-minute timer will begin. You must select your candidate and submit your vote within this time. If you do not submit within 10 minutes, your session will expire and you will need to restart the process.
            <br />
            <br />
            Depending on the type of election, you may be asked to:
            <ul style={listStyle}>
              <li><strong>First Past the Post (FPTP):</strong> Select a single candidate for your constituency</li>
              <li><strong>Additional Member System (AMS):</strong> Select a constituency candidate and a regional party vote</li>
              <li><strong>Single Transferable Vote (STV):</strong> Rank candidates in order of preference</li>
              <li><strong>Alternative Vote:</strong> Rank candidates in order of preference</li>
            </ul>
            For referendums, you will be asked to vote Yes or No on the question presented.
            <br />
            <br />
            Once you have made your selection, press "Next" to proceed to the submission stage.
          </p>

          {/* Step 5: Vote Submission and Confirmation */}
          <h3 style={h3Style}>{sectionDiamond}Step 5: Vote Submission and Confirmation</h3>
          <p style={pAfterHeaderStyle}>
            To submit your vote, press the "Submit Vote" button. Once submitted, your vote is recorded anonymously and your ballot token is marked as used to prevent duplicate submissions.
            <br />
            <br />
            If you wish to receive an email confirmation of your participation, you can tick the "I would like to receive an email confirmation" checkbox. This confirmation will be sent to the email address you provided when you registered. Please note that the confirmation only records that you voted, not how you voted.
            <br />
            <br />
            <strong>Important:</strong> Your vote is anonymous and cannot be linked to your identity. You will not be able to change your vote once it has been submitted.
          </p>
        </section>

        {/* After Voting */}
        <section style={sectionWithPaddingStyle}>
          <h2 style={sectionH2Style}>After Voting: Counting and Results</h2>
          <p style={pAfterHeaderStyle}>
            All submitted votes are tallied by the system once the voting period has closed. Results are verified and published by the Official UK Voting Platform's Election Officials.
            <br />
            <br />
            A separate voter ledger records that you have participated in the election, but this is kept entirely separate from your vote. This ensures that no one — including system administrators — can determine how you voted while still preventing any individual from voting more than once.
            <br />
            <br />
            If you have any concerns about the voting process or the accuracy of the results, you may raise them with the Election Officials through the platform.
          </p>
        </section>
      </div>
    </div>
  );
};

export default VoterVotingProcessPage;
