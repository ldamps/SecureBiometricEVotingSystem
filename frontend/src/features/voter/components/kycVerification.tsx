import { useState } from "react";
import { loadStripe } from "@stripe/stripe-js";
import { getVoterPageContentWrapperStyle, getCardStyle, getStepTitleStyle, getStepLabelStyle, PrimaryButton } from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";
import ProgressBar from "./progressBar";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL ?? "/api/v1";

type KycStatus = "" | "processing" | "verified" | "requires_input" | "canceled";

function KYCVerification({
    next,
    back,
    state,
    setState,
}: {
    next: () => void;
    back: () => void;
    state: any;
    setState: (state: any) => void;
}) {
    const { theme } = useTheme();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [sessionId, setSessionId] = useState<string>(state.kycSessionId || "");
    const [status, setStatus] = useState<KycStatus>(state.kycStatus || "");

    const startVerification = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/kyc/session`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: state.email || "" }),
            });

            if (!response.ok) {
                throw new Error("Failed to create KYC session");
            }

            const data = await response.json();
            const clientSecret = data.client_secret;
            const sid = data.session_id;

            setSessionId(sid);
            setState({ ...state, kycSessionId: sid });

            // Mock session (test mode) — skip Stripe modal, go straight to polling
            if (sid.startsWith("mock_vs_")) {
                await pollStatus(sid);
                return;
            }

            const stripe = await loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY || "");
            if (!stripe) {
                throw new Error("Failed to load Stripe");
            }

            const result = await stripe.verifyIdentity(clientSecret);

            if (result.error) {
                setError(result.error.message || "Verification failed");
                setLoading(false);
                return;
            }

            // Poll for status after modal closes
            await pollStatus(sid);
        } catch (err: any) {
            setError(err.message || "An error occurred");
        } finally {
            setLoading(false);
        }
    };

    const pollStatus = async (sid: string) => {
        try {
            const response = await fetch(`${API_BASE_URL}/kyc/session/${sid}/status`);
            if (!response.ok) {
                throw new Error("Failed to check verification status");
            }
            const data = await response.json();
            const newStatus: KycStatus = data.status || "";
            setStatus(newStatus);
            setState({ ...state, kycSessionId: sid, kycStatus: newStatus });

            if (newStatus === "processing") {
                // Continue polling every 3 seconds
                setTimeout(() => pollStatus(sid), 3000);
            }
        } catch (err: any) {
            setError(err.message || "Failed to check status");
        }
    };

    const getStatusDisplay = () => {
        switch (status) {
            case "processing":
                return (
                    <div style={{ ...getCardStyle(theme), marginBottom: "1rem", textAlign: "center" }}>
                        <p style={{ color: theme.colors.text.primary, fontSize: theme.fontSizes?.base || "1rem" }}>
                            Verification is being processed...
                        </p>
                    </div>
                );
            case "verified":
                return (
                    <div style={{
                        ...getCardStyle(theme),
                        marginBottom: "1rem",
                        backgroundColor: "#f0fff4",
                        border: `1px solid ${theme.colors.status?.success || "#38a169"}`,
                    }}>
                        <p style={{
                            color: theme.colors.status?.success || "#38a169",
                            fontWeight: 600,
                            fontSize: theme.fontSizes?.base || "1rem",
                        }}>
                            Identity verified successfully!
                        </p>
                    </div>
                );
            case "requires_input":
                return (
                    <div style={{ ...getCardStyle(theme), marginBottom: "1rem" }}>
                        <p style={{ color: theme.colors.text.primary, fontSize: theme.fontSizes?.base || "1rem" }}>
                            Verification requires additional input. Please try again.
                        </p>
                        <div style={{ marginTop: theme.spacing?.md || "1rem" }}>
                            <PrimaryButton onClick={startVerification} disabled={loading}>
                                Retry
                            </PrimaryButton>
                        </div>
                    </div>
                );
            case "canceled":
                return (
                    <div style={{ ...getCardStyle(theme), marginBottom: "1rem" }}>
                        <p style={{ color: theme.colors.text.primary, fontSize: theme.fontSizes?.base || "1rem" }}>
                            Verification was cancelled.
                        </p>
                        <div style={{ marginTop: theme.spacing?.md || "1rem" }}>
                            <PrimaryButton onClick={startVerification} disabled={loading}>
                                Retry
                            </PrimaryButton>
                        </div>
                    </div>
                );
            default:
                return null;
        }
    };

    return (
        <div style={{ ...getVoterPageContentWrapperStyle(theme), maxWidth: "100%", margin: "0 auto" }}>
            <div style={{ ...getCardStyle(theme), marginBottom: "1.75rem" }}>
                <ProgressBar step={3} theme={theme} />
                <h1 style={getStepTitleStyle(theme)}>Registration: Identity Verification (KYC)</h1>
            </div>

            <div style={{ ...getCardStyle(theme), marginBottom: "1.25rem" }}>
                <p style={getStepLabelStyle(theme)}>
                    To complete your registration, we need to verify your identity. This is done securely
                    through Stripe Identity. You will be asked to provide a photo of your passport or
                    driving licence and take a selfie.
                </p>
            </div>

            {!status && (
                <div style={{ display: "flex", justifyContent: "center", marginBottom: "1.25rem" }}>
                    <PrimaryButton onClick={startVerification} disabled={loading}>
                        {loading ? "Starting..." : "Start Verification"}
                    </PrimaryButton>
                </div>
            )}

            {error && (
                <div style={{ ...getCardStyle(theme), marginBottom: "1rem" }}>
                    <p style={{ color: theme.colors.status?.error || "#e53e3e" }}>{error}</p>
                </div>
            )}

            {getStatusDisplay()}

            <div style={{ marginTop: "1.75rem", display: "flex", justifyContent: "center", gap: theme.spacing?.md || "1rem" }}>
                <PrimaryButton onClick={back}>Back</PrimaryButton>
                <PrimaryButton onClick={next} disabled={status !== "verified"}>
                    Next
                </PrimaryButton>
            </div>
        </div>
    );
}

export default KYCVerification;
