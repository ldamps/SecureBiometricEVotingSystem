import React from "react";
import { useTheme } from "../../styles/ThemeContext";
import { getFirstSectionStyle, getLinkStyle, getListStyle, getPageTitleStyle, getSectionH2Style, getVoterPageContentWrapperStyle } from "../../styles/ui";

const VoterVotingProcessPage: React.FC = () => {
  const { theme } = useTheme();
  const pageTitleStyle = getPageTitleStyle(theme);
  const wrapperStyle = getVoterPageContentWrapperStyle(theme);
  const firstSectionStyle = getFirstSectionStyle(theme);
  const sectionH2Style = getSectionH2Style(theme);
  const listStyle = getListStyle(theme);
  const linkStyle = getLinkStyle(theme);
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
          The Official UK Voting Platform allows for a fully online voting process.
        </p>
        <h2 style={sectionH2Style}>The Step-by-Step Voting Process</h2>
        <p style={firstSectionStyle}>
            This platform provides a secure and simple way for eligible voters to register, verify their identity, and cast their vote electronically. Biometric authentication ensures that only authorised voters can access the system, while the design of the platform guarantees that every vote remains anonymous. 
          <ol style={listStyle}>
            
            <li>
                <strong>Register to Vote</strong>
                <br />
                In order to vote, you must first be registered to vote on this platform. 
                <br />
                <br />
                Before you vote, please ensure your registration details are up-to-date. You may update your registration details at any time on the platform by going to the <a href="/voter/manage-registration" style={linkStyle}>manage your voting details</a> page.
            </li>

            <li>
                <strong>The Voting Process</strong>
                <br />
                The voting process will take around 5-10 minutes.
                <br />
                You can begin the voting process from the <a href="/voter/voting" style={linkStyle}>Begin Vote</a> page.
                <br />
                <br />
                In the voting process, you will be asked to:
                <ol style={listStyle}>
                    <li>
                        <strong>Select an Election</strong>
                        <br />
                        The first thing you will be asked to do is select the election you wish to vote in. 
                        <br />
                        You will be given a list of elections to choose from.
                        <br />
                        Once you have selected the election you wish to vote in, you can press the "Next" button to continue.
                    </li>
                    <li>
                        <strong>Confirming Identity to Vote</strong>
                        <br />
                        Once you have selected the election you wish to vote in, you will be asked to confirm your identity.
                        <br />
                        You will be asked to provide your:
                        <ul style={listStyle}>
                            <li>Full Name</li>
                            <li>Address line 1</li>
                            <li>Address line 2</li>
                            <li>City / Town</li>
                            <li>Postcode</li>
                        </ul>
                        Once you have entered your registration details, you can press the "Next" button to continue.
                        <br />
                        If your registrations details are not correct, including if:
                        <ul style={listStyle}>
                            <li>Your name is not on the electoral roll</li>
                            <li>Your address is outside the constituency of your selected election</li>
                            <li>Your address and name do not match the electoral roll</li>
                        </ul>
                        You will be unable to complete the voting process.
                    </li>
                    <li>
                        <strong>Biometric Verification</strong>
                        <br />
                        Once your identity has been confirmed on the electoral roll, you will be asked to verify your identity using biometric information.
                        <br />
                        Ear and facial biometricc verification will be used to confirm your identity. This is to ensure that you the voter is who you say you are, with the aim to reduce the risk of electoral fraud. 
                        <br />
                        <br />
                        You will be given 3 attempts to verify your identity. If you fail to verify your identity, your account will be locked for a period of time.
                        <br />
                        If you are unable to verify your identity, you will be unable to complete the voting process.
                        <br />
                        <br />
                        Once you have verified your identity, you can press the "Next" button to continue.
                    </li>
                    <li>
                        <strong>Candidate Selection</strong>
                        <br />
                        Once you have entered this stage, a 10 minute timer will begin. You will have 10 minutes to select a candidate and submit your vote. If you do not submit your vote within 10 minutes, your vote will not be submitted and you will need to start the process again.
                        <br />
                        <br />
                        You will be given a list of candidates to choose from.
                        <br />
                        Once you have selected the candidate you wish to vote for, you can press the "Next" button to 
                    </li>
                    <li>
                        <strong>Vote Submission + Confirmation</strong>
                        <br />
                        To submit your vote, you will need to press the "Submit Vote" button.
                        <br />
                        <br />
                        If you wish to receive an email confirmation of your vote, you can tick the "I would like to receive an email confirmation" checkbox.
                        <br />
                        This email confirmation, if you wish to receive it, will be sent to the email address you provided when you registered to vote.
                        <br />
                        <br />
                        We would like to remind you that your vote is anonymous and will not be linked to your identity.
                        Additionally, you will not be able to change your vote once you have submitted it.
                    </li>
                </ol>
            </li>
            
            <li>
                <strong>Vote Counting + Result Verification</strong>
                <br />
                All submitted votes will be tallied internally by the system. Once the vote has closed, the results will be verified and published by the Official UK Voting Platform's Election Officials.
                <br />
                It is our biggest priority to ensure the integrity of the voting process. So if you have any concerns about the voting process and the accuracy of the results, please contact xxx.
            </li>
          </ol>
        </p>
      </div>
    </div>
  );
};

export default VoterVotingProcessPage;
