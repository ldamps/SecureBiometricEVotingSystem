import { useState } from "react";
import { getCardStyle, getStepDescStyle, getStepTitleStyle, getStepLabelStyle, getVoterPageContentWrapperStyle } from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";
import ProgressBar from "./progressBar";
import { PrimaryButton } from "../../../styles/ui";
import { useNavigate } from "react-router-dom";
import { VoterApiRepository } from "../repositories/voter-api.repository";
import { NationalityCategory } from "../model/voter.model";

const voterApi = new VoterApiRepository();

/**
 * Check whether all registration steps have been completed and the voter
 * is legally eligible to vote.  Returns an array of issues (empty = eligible).
 */
function checkEligibility(state: any): string[] {
    const issues: string[] = [];

    // Step 2: Identity verification (KYC)
    if (state.kycStatus !== "verified") {
        issues.push("Identity verification (KYC) has not been completed.");
    }

    // Step 2: Nationality
    const hasBritish = !!state.nationalityBritish;
    const hasIrish = !!state.nationalityIrish;
    const hasOther = !!state.nationalityOtherCountry;

    if (!hasBritish && !hasIrish && !hasOther) {
        issues.push("No nationality has been selected.");
    }

    if (!hasBritish && !hasIrish && hasOther) {
        issues.push(
            "Citizens of countries other than the UK or Ireland may only vote " +
            "if they are qualifying Commonwealth or EU citizens with the right to remain."
        );
    }

    // Step 2: Identification method
    const idMethod = state.identificationMethod || "";
    if (!idMethod) {
        issues.push("No identification method has been selected.");
    } else if (idMethod === "ni" && !state.nationalInsuranceNumber?.trim()) {
        issues.push("National Insurance Number has not been provided.");
    } else if (idMethod === "passport" && !state.passportNumber?.trim()) {
        issues.push("Passport number has not been provided.");
    }

    // Step 3: Address
    if (!state.addressLine1?.trim()) {
        issues.push("Current address has not been provided.");
    }

    // Step 3: Address verification
    if (!state.addressVerified) {
        issues.push("Proof of address has not been verified. Please go back and upload a valid document.");
    }

    // Step 4: Biometric enrollment
    if (!state.biometricEnrolled) {
        issues.push("Biometric enrollment has not been completed. Please link your mobile device and enroll your face and ear biometrics.");
    }

    return issues;
}

/**
 * Derive the nationality category from the registration state.
 */
function deriveNationalityCategory(state: any): NationalityCategory {
    if (state.nationalityBritish) return NationalityCategory.BRITISH_CITIZEN;
    if (state.nationalityIrish) return NationalityCategory.IRISH_CITIZEN;
    return NationalityCategory.OTHER;
}

function RegistrationConfirmation({next, back, state, setState}: {next: () => void, back: () => void, state: any, setState: (state: any) => void}) {
    const { theme } = useTheme();
    const navigate = useNavigate();
    const [confirmed, setConfirmed] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState<string | null>(null);

    const eligibilityIssues = checkEligibility(state);
    const isEligible = eligibilityIssues.length === 0;

    const handleFinish = async () => {
        if (!isEligible || submitting) return;
        setSubmitting(true);
        setSubmitError(null);

        try {
            const voterId = state.voterId;

            // Update voter nationality if needed (address + status are handled
            // automatically by the backend during address verification and
            // biometric enrollment)
            await voterApi.updateVoter(voterId, {
                nationality_category: deriveNationalityCategory(state),
            });

            navigate("/voter/landing");
        } catch (err: any) {
            setSubmitError(err.message || "Registration failed. Please try again.");
            setSubmitting(false);
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
                        Please go back and complete all required steps before finishing your registration.
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
                        All checks passed — you are eligible to register to vote.
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

            {submitError && (
                <p style={{ color: theme.colors.status.error, marginTop: theme.spacing.sm }}>
                    {submitError}
                </p>
            )}

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
                <PrimaryButton
                    onClick={handleFinish}
                    disabled={!confirmed || !isEligible || submitting}
                >
                    {submitting ? "Registering\u2026" : "Finish"}
                </PrimaryButton>
            </div>
        </div>
    )
}

export default RegistrationConfirmation;
