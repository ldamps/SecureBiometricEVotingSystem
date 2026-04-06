// Voting Step: Referendum Answer Selection (Yes / No)

import { useState, useEffect } from "react";
import ProgressBar from "./progressBar";
import {
    getVoterPageContentWrapperStyle,
    getCardStyle,
    getStepTitleStyle,
    getStepDescStyle,
    getStepLabelStyle,
    PrimaryButton,
} from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";
import { ReferendumApiRepository } from "../../referendum/repositories/referendum-api.repository";
import type { Referendum } from "../../referendum/model/referendum.model";

const referendumApi = new ReferendumApiRepository();

function ReferendumAnswerSelection({
    back,
    next,
    state,
    setState,
}: {
    back: () => void;
    next: () => void;
    state: any;
    setState: (state: any) => void;
}) {
    const { theme } = useTheme();
    const [referendum, setReferendum] = useState<Referendum | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [validationError, setValidationError] = useState<string | null>(null);

    useEffect(() => {
        if (!state.referendum) return;
        setLoading(true);
        referendumApi
            .getReferendum(state.referendum)
            .then((r) => {
                setReferendum(r);
                setError(null);
            })
            .catch((err: Error) => setError(err.message || "Failed to load referendum details."))
            .finally(() => setLoading(false));
    }, [state.referendum]);

    const choice: string = state.referendumChoice || "";

    const handleNext = () => {
        if (!choice) {
            setValidationError("Please select Yes or No before continuing.");
            return;
        }
        setValidationError(null);
        next();
    };

    return (
        <div style={{ ...getVoterPageContentWrapperStyle(theme), maxWidth: "100%", margin: "0 auto" }}>
            <div style={{ ...getCardStyle(theme), marginBottom: "1.75rem" }}>
                <ProgressBar step={4} theme={theme} />
            </div>

            <h1 style={getStepTitleStyle(theme)}>Referendum</h1>

            {loading && <p style={{ color: theme.colors.text.secondary }}>Loading…</p>}
            {error && <p style={{ color: theme.colors.status.error }}>{error}</p>}

            {referendum && (
                <>
                    <div style={{ ...getCardStyle(theme), marginBottom: "1.25rem" }}>
                        <h2 style={{ ...getStepLabelStyle(theme), fontSize: theme.fontSizes.lg, marginBottom: theme.spacing.sm }}>
                            {referendum.title}
                        </h2>
                        {referendum.description && (
                            <p style={{ color: theme.colors.text.secondary, fontSize: theme.fontSizes.sm, marginBottom: theme.spacing.md }}>
                                {referendum.description}
                            </p>
                        )}
                        <p style={{ ...getStepDescStyle(theme), fontWeight: 600, marginBottom: 0 }}>
                            {referendum.question}
                        </p>
                    </div>

                    {validationError && (
                        <p style={{ color: theme.colors.status.error, fontSize: "0.875rem", marginBottom: "0.75rem" }}>
                            {validationError}
                        </p>
                    )}

                    {["YES", "NO"].map((option) => (
                        <label
                            key={option}
                            style={{
                                ...getCardStyle(theme),
                                marginBottom: "1rem",
                                display: "flex",
                                alignItems: "center",
                                gap: theme.spacing.md,
                                cursor: "pointer",
                                border: choice === option
                                    ? `2px solid ${theme.colors.primary || theme.colors.button}`
                                    : undefined,
                            }}
                        >
                            <input
                                type="radio"
                                name="referendumChoice"
                                value={option}
                                checked={choice === option}
                                onChange={() => setState({ ...state, referendumChoice: option })}
                                style={{ accentColor: theme.colors.button }}
                            />
                            <span style={{ fontSize: theme.fontSizes.lg, fontWeight: 600, color: theme.colors.text.primary }}>
                                {option === "YES" ? "Yes" : "No"}
                            </span>
                        </label>
                    ))}
                </>
            )}

            <div style={{ marginTop: "1.75rem", display: "flex", justifyContent: "center", gap: theme.spacing?.md ?? theme.spacing?.sm ?? "1rem"  }}>
                <PrimaryButton onClick={back}>Back</PrimaryButton>
                <PrimaryButton onClick={handleNext} disabled={loading}>
                    Next
                </PrimaryButton>
            </div>
        </div>
    );
}

export default ReferendumAnswerSelection;
