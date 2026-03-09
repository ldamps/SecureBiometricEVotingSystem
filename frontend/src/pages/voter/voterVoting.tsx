// Voting page - Voter voting page

import React from "react";
import { useTheme } from "../../styles/ThemeContext";
import PrimaryButton from "../../components/PrimaryButton";
import { useNavigate } from "react-router-dom";
import {
  VoterPageWrapper,
  VoterPageHeader,
  VoterFirstSection,
  VoterCard,
  VoterLink,
  getListStyle,
  getRegistrationCardTextStyle,
  getRegistrationListStyle,
} from "../../features/voter/components";

const VoteCastingPage: React.FC = () => {
    const { theme } = useTheme();
    const navigate = useNavigate();
    const listStyle = getListStyle(theme);
    const cardTextStyle = getRegistrationCardTextStyle(theme);
    const cardListStyle = getRegistrationListStyle(theme);

    return (
        <div className="voter-voting-page">
            <VoterPageWrapper className="voter-voting-page">
                <VoterPageHeader title="Vote" />
                <VoterFirstSection as="div">
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
                    To know more about the voting process, please visit the <VoterLink href="/voter/voting-process">The Voting Process</VoterLink> page.
                    <br />
                    <br />
                    <VoterCard title="Please note">
                        <ul style={cardListStyle}>
                            <li style={cardTextStyle}>You must be registered and eligible to vote in order to cast your vote.
                                <br />
                                If you have not registered to vote yet, you can <VoterLink href="/voter/register">register to vote here</VoterLink>.
                            </li>
                            <li style={cardTextStyle}>Your registrations need to be up-to-date.
                                <br />
                                If you have changed your name, address or nationality, you need to <VoterLink href="/voter/manage-registration">update your registration details</VoterLink>.
                            </li>
                            <li style={cardTextStyle}>You can only vote once.
                                <br />
                                You are only eligible to vote in elections run in your current constituency.
                            </li>
                            <li style={cardTextStyle}>You are only eligible to vote in elections run in your current constituency.</li>
                            <li style={cardTextStyle}>Once verified, you will have 10 minutes to cast your vote. If you do not cast your vote within 10 minutes, you will need to start the process again.</li>
                        </ul>
                    </VoterCard>
                    <br />
                    <PrimaryButton onClick={() => navigate("/voter/landing")}>Vote</PrimaryButton>
                </VoterFirstSection>
            </VoterPageWrapper>
        </div>
    )
};

export default VoteCastingPage;