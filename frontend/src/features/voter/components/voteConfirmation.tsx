// Voting Step: Vote Confirmation & Submission

import { useState } from "react";
import ProgressBar from "./progressBar";
import {
    getVoterPageContentWrapperStyle,
    getCardStyle,
    getStepTitleStyle,
    getStepDescStyle,
    PrimaryButton,
} from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";
import { useNavigate } from "react-router-dom";
import { VotingApiRepository } from "../repositories/voting-api.repository";
import type { RankedPreference } from "../repositories/voting-api.repository";

const votingApi = new VotingApiRepository();

function VoteConfirmation({
    next,
    state,
    setState,
}: {
    next: () => void;
    state: any;
    setState: (state: any) => void;
}) {
    const { theme } = useTheme();
    const navigate = useNavigate();
    const [sendEmail, setSendEmail] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [submitted, setSubmitted] = useState(false);
    const [receiptCode, setReceiptCode] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const isReferendum = Boolean(state.referendum);

    const handleSubmit = async () => {
        if (submitting || submitted) return;
        setSubmitting(true);
        setError(null);

        try {
            if (isReferendum) {
                const result = await votingApi.castReferendumVote({
                    voter_id: state.voterId,
                    referendum_id: state.referendum,
                    choice: state.referendumChoice,
                    send_email_confirmation: sendEmail,
                });
                setReceiptCode(result.receipt_code);
            } else {
                // Build ranked preferences from state.rankings if present
                let rankedPreferences: RankedPreference[] | undefined;
                if (state.rankings && Object.keys(state.rankings).length > 0) {
                    rankedPreferences = Object.entries(state.rankings as Record<string, number>).map(
                        ([candidateId, rank]) => ({
                            candidate_id: candidateId,
                            preference_rank: rank,
                        }),
                    );
                }

                const result = await votingApi.castElectionVote({
                    voter_id: state.voterId,
                    election_id: state.election,
                    constituency_id: state.constituencyId,
                    candidate_id: state.candidateId || undefined,
                    party_id: state.partyId || undefined,
                    ranked_preferences: rankedPreferences,
                    send_email_confirmation: sendEmail,
                });
                setReceiptCode(result.receipt_code);
            }
            setSubmitted(true);
        } catch (err: any) {
            setError(err.message || "Failed to submit your vote. Please try again.");
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div style={{ ...getVoterPageContentWrapperStyle(theme), maxWidth: "100%", margin: "0 auto" }}>
            <div style={{ ...getCardStyle(theme), marginBottom: "1.75rem" }}>
                <ProgressBar step={5} theme={theme} />
            </div>

            {!submitted ? (
                <>
                    <h1 style={getStepTitleStyle(theme)}>Confirm Your Vote</h1>
                    <p style={getStepDescStyle(theme)}>
                        Please review your selection before submitting. Once submitted, your vote <strong>cannot be changed or revoked</strong>.
                    </p>

                    <div style={{ ...getCardStyle(theme), marginBottom: "1rem" }}>
                        <p style={{ margin: 0, fontSize: theme.fontSizes.base, color: theme.colors.text.primary }}>
                            {isReferendum
                                ? `Referendum answer: ${state.referendumChoice}`
                                : state.candidateId
                                    ? "Your candidate selection has been recorded."
                                    : state.rankings && Object.keys(state.rankings).length > 0
                                        ? `You have ranked ${Object.keys(state.rankings).length} candidate(s).`
                                        : state.partyId
                                            ? "Your party selection has been recorded."
                                            : "Your selection has been recorded."
                            }
                        </p>
                    </div>

                    <label
                        style={{
                            ...getCardStyle(theme),
                            marginBottom: "1.75rem",
                            display: "flex",
                            alignItems: "center",
                            gap: theme.spacing.md,
                            cursor: "pointer",
                        }}
                    >
                        <input
                            type="checkbox"
                            checked={sendEmail}
                            onChange={(e) => setSendEmail(e.target.checked)}
                            style={{ accentColor: theme.colors.button }}
                        />
                        <span style={{ fontSize: theme.fontSizes.base, color: theme.colors.text.primary }}>
                            I would like to receive an email confirmation
                        </span>
                    </label>

                    {error && (
                        <div style={{
                            ...getCardStyle(theme),
                            marginBottom: "1rem",
                            backgroundColor: "#fef2f2",
                            border: `1px solid ${theme.colors.status.error}`,
                        }}>
                            <p style={{ color: theme.colors.status.error, fontSize: "0.9rem", fontWeight: 600, margin: 0 }}>
                                {error}
                            </p>
                        </div>
                    )}

                    <div style={{ display: "flex", justifyContent: "center" }}>
                        <PrimaryButton disabled={submitting} onClick={handleSubmit}>
                            {submitting ? "Submitting..." : "Submit Vote"}
                        </PrimaryButton>
                    </div>
                </>
            ) : (
                <>
                    <h1 style={getStepTitleStyle(theme)}>Thank You for Voting!</h1>
                    <p style={getStepDescStyle(theme)}>
                        Your vote has been cast successfully and recorded anonymously.
                    </p>

                    {receiptCode && (
                        <div style={{ ...getCardStyle(theme), marginBottom: "1.25rem" }}>
                            <p style={{ margin: 0, fontSize: theme.fontSizes.sm, color: theme.colors.text.secondary, marginBottom: theme.spacing.xs }}>
                                Your receipt code (save this for verification):
                            </p>
                            <p style={{
                                margin: 0,
                                fontSize: theme.fontSizes.base,
                                fontWeight: 700,
                                color: theme.colors.text.primary,
                                fontFamily: "monospace",
                                wordBreak: "break-all",
                            }}>
                                {receiptCode}
                            </p>
                        </div>
                    )}

                    {sendEmail && (
                        <p style={{ fontSize: theme.fontSizes.sm, color: theme.colors.text.secondary, marginBottom: theme.spacing.md }}>
                            A confirmation email will be sent to your registered email address.
                        </p>
                    )}

                    <div style={{ display: "flex", justifyContent: "center" }}>
                        <PrimaryButton onClick={() => navigate("/voter/landing")}>Finish</PrimaryButton>
                    </div>
                </>
            )}
        </div>
    );
}

export default VoteConfirmation;
