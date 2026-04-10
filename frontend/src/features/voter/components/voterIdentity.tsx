// Voting Step: Voter Identity

import {
    PrimaryButton,
    getFirstSectionStyle,
    getPageTitleStyle,
    getCardStyle,
    getVoterPageContentWrapperStyle,
    getStepTitleStyle,
    getStepDescStyle,
    getStepFormInputStyle,
    getStepLabelStyle,
    getErrorAlertStyle,
} from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";
import ProgressBar from "./progressBar";
import { useState } from "react";
import { VoterApiRepository } from "../repositories/voter-api.repository";

const voterApi = new VoterApiRepository();

function VoterIdentity({ next, state, setState, progressStep = 1, showProgressBar = true, usePageLayout = false }: { next: () => void; state: any; setState: (state: any) => void; progressStep?: number; showProgressBar?: boolean; usePageLayout?: boolean }) {
    const { theme } = useTheme();

    const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
    const [submitting, setSubmitting] = useState(false);

    const fields = [
        { key: "name", label: "Full Name", placeholder: "e.g. Jane Smith", required: true },
        { key: "addr1", label: "Address Line 1", placeholder: "House number and street", required: true },
        { key: "addr2", label: "Address Line 2", placeholder: "Flat, apartment, etc.", required: false },
        { key: "city", label: "City / Town", placeholder: "e.g. London", required: true },
        { key: "postcode", label: "Postcode", placeholder: "e.g. SW1A 1AA", required: false },
    ];

    const handleNext = async () => {
        if (submitting) return;

        const errors: Record<string, string> = {};
        if (!state.name?.trim()) errors.name = "Full name is required.";
        if (!state.addr1?.trim()) errors.addr1 = "Address line 1 is required.";
        if (!state.city?.trim()) errors.city = "City / Town is required.";
        const pc = (state.postcode || "").trim();
        if (pc && !/^[A-Za-z]{1,2}\d[A-Za-z\d]?\s?\d[A-Za-z]{2}$/i.test(pc)) {
            errors.postcode = "Please enter a valid UK postcode (e.g. SW1A 1AA).";
        }

        setValidationErrors(errors);
        if (Object.keys(errors).length > 0) return;

        setSubmitting(true);
        try {
            const result = await voterApi.verifyIdentity({
                full_name: state.name.trim(),
                address_line1: state.addr1.trim(),
                address_line2: state.addr2?.trim() || undefined,
                city: state.city.trim(),
                postcode: state.postcode?.trim() || undefined,
            });

            if (result.verified && result.voter_id) {
                // Fetch voter details to get their constituency_id
                const voter = await voterApi.getVoter(result.voter_id);
                setState({ ...state, voterId: result.voter_id, constituencyId: voter.constituency_id });
                next();
            } else {
                setValidationErrors({
                    submit: result.message || "We could not find a registered voter matching these details. Please check your information and try again.",
                });
            }
        } catch (err: any) {
            let message: string;
            if (err.code === "TIMEOUT") {
                message = "The identity check is taking too long. Please check your details are correct and try again.";
            } else if (err.code === "NETWORK_ERROR" || err.status === 0) {
                message = "Unable to reach the server. Please check your internet connection and try again.";
            } else if (err.status === 404) {
                message = "We could not find a registered voter matching these details. Please double-check your name, address, and postcode.";
            } else if (err.status === 422) {
                message = "Some of the details you entered are invalid. Please correct them and try again.";
            } else if (err.status && err.status >= 500) {
                message = "The server encountered an error. Please try again in a few moments.";
            } else {
                message = "Something went wrong while verifying your identity. Please try again.";
            }
            setValidationErrors({ submit: message });
        } finally {
            setSubmitting(false);
        }
    };

    const formContent = (
        <>
            {!usePageLayout && (
                <>
                    {showProgressBar && (
                        <div style={{...getCardStyle(theme), marginBottom: "1.75rem"}}>
                            <ProgressBar step={progressStep} theme={theme} />
                        </div>
                    )}
                    <h1 style={getStepTitleStyle(theme)}>Confirm Your Identity</h1>
                    <p style={getStepDescStyle(theme)}>Please confirm your identity by providing the following information.</p>
                </>
            )}
            {usePageLayout && <p style={{ marginBottom: theme.spacing.md }}>Please confirm your identity by providing the following information.</p>}

            {validationErrors.submit && (
                <div style={{
                    ...getCardStyle(theme),
                    ...getErrorAlertStyle(theme),
                    marginBottom: "1rem",
                }}>
                    <p style={{ color: theme.colors.status.error, fontSize: "0.9rem", fontWeight: 600, margin: 0 }}>
                        {validationErrors.submit}
                    </p>
                </div>
            )}

            {fields.map(field => (
                <div key={field.key} style={{...getCardStyle(theme), marginBottom: "1rem"}}>
                    <label htmlFor={field.key} style={getStepLabelStyle(theme)}>
                        {field.label}
                        {field.required && <span style={{ color: theme.colors.status.error }}> *</span>}
                    </label>
                    {validationErrors[field.key] && (
                        <p style={{ color: theme.colors.status.error, fontSize: "0.875rem", marginTop: "0.25rem", marginBottom: "0.25rem" }}>
                            {validationErrors[field.key]}
                        </p>
                    )}
                    <input
                        type="text"
                        id={field.key}
                        name={field.key}
                        placeholder={field.placeholder}
                        value={state[field.key] || ""}
                        onChange={(e) => setState({...state, [field.key]: e.target.value})}
                        style={getStepFormInputStyle(theme)}
                    />
                </div>
            ))}
            <div style={{ marginTop: "1.75rem", display: "flex", justifyContent: usePageLayout ? "flex-start" : "center", gap: theme.spacing.md }}>
                <PrimaryButton disabled={submitting} onClick={handleNext}>
                    {submitting ? "Verifying..." : "Next"}
                </PrimaryButton>
            </div>
        </>
    );

    if (usePageLayout) {
        return (
            <div className="voter-update-registration-page voter-page-content" style={getVoterPageContentWrapperStyle(theme)}>
                <header>
                    <h1 style={getPageTitleStyle(theme)}>Confirm your identity</h1>
                </header>
                <section style={getFirstSectionStyle(theme)}>
                    {formContent}
                </section>
            </div>
        );
    }

    return (
        <div style={{ ...getVoterPageContentWrapperStyle(theme), maxWidth: "100%", margin: "0 auto" }}>
            {formContent}
        </div>
    );
}

export default VoterIdentity;
