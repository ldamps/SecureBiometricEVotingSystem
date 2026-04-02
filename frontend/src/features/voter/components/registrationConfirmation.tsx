import { useState } from "react";
import { getCardStyle, getStepDescStyle, getStepTitleStyle, getStepLabelStyle, getVoterPageContentWrapperStyle } from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";
import ProgressBar from "./progressBar";
import { PrimaryButton } from "../../../styles/ui";
import { useNavigate } from "react-router-dom";

/**
 * Check whether the voter is legally eligible to vote based on nationality
 * and KYC verification status. Returns an array of issues (empty = eligible).
 */
function checkEligibility(state: any): string[] {
    const issues: string[] = [];

    // Must have completed identity verification
    if (state.kycStatus !== "verified") {
        issues.push("Identity verification (KYC) has not been completed.");
    }

    // Must have a nationality that grants voting rights in the UK
    const hasBritish = !!state.nationalityBritish;
    const hasIrish = !!state.nationalityIrish;
    const hasOther = !!state.nationalityOtherCountry;

    if (!hasBritish && !hasIrish && !hasOther) {
        issues.push("No nationality has been selected.");
    }

    // If only "other" nationality with no British/Irish — eligibility is uncertain
    if (!hasBritish && !hasIrish && hasOther) {
        issues.push(
            "Citizens of countries other than the UK or Ireland may only vote " +
            "if they are qualifying Commonwealth or EU citizens with the right to remain."
        );
    }

    // Must have provided either NI or passport
    const idMethod = state.identificationMethod || "";
    if (!idMethod) {
        issues.push("No identification method has been selected.");
    } else if (idMethod === "ni" && !state.nationalInsuranceNumber?.trim()) {
        issues.push("National Insurance Number has not been provided.");
    } else if (idMethod === "passport" && !state.passportNumber?.trim()) {
        issues.push("Passport number has not been provided.");
    }

    return issues;
}

function RegistrationConfirmation({next, back, state, setState}: {next: () => void, back: () => void, state: any, setState: (state: any) => void}) {
    const { theme } = useTheme();
    const navigate = useNavigate();
    const [confirmed, setConfirmed] = useState(false);

    const eligibilityIssues = checkEligibility(state);
    const isEligible = eligibilityIssues.length === 0;

    const handleFinish = () => {
        if (isEligible) {
            navigate("/voter/landing");
        } else {
            /*
             * TODO: When the eligibility check fails, create a case/task in the
             * system so the local electoral registration office can contact the
             * voter with further information. This should:
             *   1. POST to a backend endpoint (e.g. POST /voter/{voter_id}/eligibility-review)
             *      that stores the voter's details and the specific issues found.
             *   2. Notify the relevant electoral office (based on constituency).
             *   3. Set the voter's registration_status to "pending_review".
             *   4. Send an email to the voter explaining that their registration is
             *      under review and they will be contacted by their local office.
             */
            navigate("/voter/landing");
        }
    };

    return (
        <div style={{ ...getVoterPageContentWrapperStyle(theme), maxWidth: "100%", margin: "0 auto" }}>
            <div style={{ ...getCardStyle(theme), marginBottom: "1.75rem" }}>
                <ProgressBar step={5} theme={theme} />
                <h1 style={getStepTitleStyle(theme)}>Registration: Finishing Up</h1>
            </div>

            {/* Eligibility check result */}
            {!isEligible && (
                <div style={{
                    ...getCardStyle(theme),
                    marginBottom: "1.25rem",
                    backgroundColor: "#fffbeb",
                    border: "1px solid #f59e0b",
                }}>
                    <p style={{ ...getStepLabelStyle(theme), color: "#b45309", marginBottom: "0.5rem" }}>
                        Eligibility check — action required
                    </p>
                    <ul style={{ margin: 0, paddingLeft: "1.25rem", fontSize: "0.9rem", color: "#92400e" }}>
                        {eligibilityIssues.map((issue, i) => (
                            <li key={i} style={{ marginBottom: "0.35rem" }}>{issue}</li>
                        ))}
                    </ul>
                    <p style={{ fontSize: "0.85rem", color: "#92400e", marginTop: "0.75rem" }}>
                        You can still submit your registration. Your local electoral registration office
                        will be notified and will contact you with further information.
                    </p>
                </div>
            )}

            {isEligible && (
                <div style={{
                    ...getCardStyle(theme),
                    marginBottom: "1.25rem",
                    backgroundColor: "#f0fff4",
                    border: "1px solid #38a169",
                }}>
                    <p style={{ color: "#38a169", fontWeight: 600, fontSize: "0.9rem" }}>
                        Eligibility check passed — you are eligible to register to vote.
                    </p>
                </div>
            )}

            <p style={getStepDescStyle(theme)}>
                Before you finish, please ensure all the information you have provided is correct and is your own information.
                <br />
                You may not register to vote on behalf of someone else.
                <br />
                <br />
                This information will be used to verify your identity during elections.
                <br />
                <br />
                You may update your registration details at any time on the platform by going to the manage your voting details page.
                <br />
                <br />
                Once you have finished this process, you will receive an email confirmation of your registration.
                <br />
                You will receive another email when your registration has been confirmed and you can start voting!
            </p>
            <label
                style={{
                    color: theme.colors.text.primary,
                    marginBottom: "1.75rem",
                    display: "flex",
                    alignItems: "center",
                    gap: theme.spacing.md,
                    cursor: "pointer",
                }}
            >
                <input
                    type="checkbox"
                    name="emailConfirmation"
                    id="emailConfirmation"
                    checked={confirmed}
                    onChange={(e) => setConfirmed(e.target.checked)}
                    style={{ accentColor: theme.colors.button }}
                />
                <span style={{ fontSize: theme.fontSizes.base, color: theme.colors.text.primary }}>I confirm that the information I have provided is correct and is my own information.</span>
            </label>
            {/* Navigation */}
            <div style={{ marginTop: "1.75rem", display: "flex", justifyContent: "center", gap: theme.spacing.md }}>
                <PrimaryButton onClick={back}>Back</PrimaryButton>
                <PrimaryButton onClick={handleFinish} disabled={!confirmed}>Finish</PrimaryButton>
            </div>
        </div>
    )
}

export default RegistrationConfirmation;