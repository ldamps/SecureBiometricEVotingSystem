// Email code verification — alternative to biometric verification
// for updating voter registration details (e.g. lost phone).

import { useState, useCallback } from "react";
import {
    getVoterPageContentWrapperStyle,
    getCardStyle,
    getStepTitleStyle,
    getStepDescStyle,
    getStepFormInputStyle,
    getStepLabelStyle,
    getFirstSectionStyle,
    getPageTitleStyle,
    getErrorAlertStyle,
    getSuccessAlertStyle,
    PrimaryButton,
    SecondaryButton,
} from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";
import { VoterApiRepository } from "../repositories/voter-api.repository";

const voterApi = new VoterApiRepository();

function EmailCodeVerification({
    next,
    back,
    state,
    setState,
    usePageLayout = false,
}: {
    next: () => void;
    back: () => void;
    state: any;
    setState: (state: any) => void;
    usePageLayout?: boolean;
}) {
    const { theme } = useTheme();

    const [step, setStep] = useState<"send" | "verify" | "verified">("send");
    const [code, setCode] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [info, setInfo] = useState<string | null>(null);

    const voterId = state.voterId as string;

    const handleSendCode = useCallback(async () => {
        if (!voterId) return;
        setLoading(true);
        setError(null);
        setInfo(null);

        try {
            const result = await voterApi.sendEmailVerificationCode(voterId);
            if (result.sent) {
                setStep("verify");
                setInfo(result.message);
            } else {
                setError(result.message);
            }
        } catch (err: any) {
            setError(err.message || "Failed to send verification code. Please try again.");
        } finally {
            setLoading(false);
        }
    }, [voterId]);

    const handleVerifyCode = useCallback(async () => {
        if (!voterId || !code.trim()) return;
        setLoading(true);
        setError(null);

        try {
            const result = await voterApi.verifyEmailCode(voterId, code.trim());
            if (result.verified) {
                setState({ ...state, biometricVerified: true });
                setStep("verified");
            } else {
                setError(result.message);
            }
        } catch (err: any) {
            setError(err.message || "Verification failed. Please try again.");
        } finally {
            setLoading(false);
        }
    }, [voterId, code, state, setState]);

    const handleResend = useCallback(async () => {
        setCode("");
        setError(null);
        await handleSendCode();
    }, [handleSendCode]);

    const content = (
        <>
            {!usePageLayout && (
                <h1 style={getStepTitleStyle(theme)}>Email Verification</h1>
            )}

            <div style={{ ...getCardStyle(theme), marginBottom: "1.25rem" }}>
                {step === "send" && (
                    <>
                        <p style={getStepDescStyle(theme)}>
                            If you cannot verify with your biometrics (e.g. lost or replaced phone),
                            we can send a 6-digit verification code to your registered email address instead.
                        </p>
                        <p style={{ ...getStepDescStyle(theme), marginTop: theme.spacing.sm }}>
                            The code will expire after 10 minutes.
                        </p>
                    </>
                )}

                {step === "verify" && (
                    <>
                        <p style={getStepDescStyle(theme)}>
                            A 6-digit code has been sent to your registered email address.
                            Please check your inbox (and spam folder) and enter the code below.
                        </p>

                        <div style={{ marginTop: theme.spacing.md }}>
                            <label htmlFor="verificationCode" style={getStepLabelStyle(theme)}>
                                Verification code
                            </label>
                            <input
                                type="text"
                                id="verificationCode"
                                name="verificationCode"
                                placeholder="e.g. 123456"
                                maxLength={6}
                                value={code}
                                onChange={(e) => {
                                    const val = e.target.value.replace(/\D/g, "").slice(0, 6);
                                    setCode(val);
                                }}
                                style={{
                                    ...getStepFormInputStyle(theme),
                                    letterSpacing: "0.3em",
                                    fontSize: "1.25rem",
                                    textAlign: "center",
                                    maxWidth: "200px",
                                }}
                                inputMode="numeric"
                                autoComplete="one-time-code"
                            />
                        </div>
                    </>
                )}

                {step === "verified" && (
                    <div style={{ ...getSuccessAlertStyle(theme) }}>
                        <strong>Email verified</strong>
                        <p style={{ margin: `${theme.spacing.xs} 0 0 0`, fontSize: "0.9rem" }}>
                            Your identity has been confirmed via email verification code.
                        </p>
                    </div>
                )}

                {error && (
                    <div style={{ ...getErrorAlertStyle(theme), marginTop: theme.spacing.md }}>
                        <p style={{ color: theme.colors.status.error, fontSize: "0.9rem", fontWeight: 600, margin: 0 }}>
                            {error}
                        </p>
                    </div>
                )}

                {info && step === "verify" && !error && (
                    <p style={{ color: theme.colors.status.success, marginTop: theme.spacing.sm, fontSize: "0.9rem" }}>
                        {info}
                    </p>
                )}
            </div>

            <div style={{
                marginTop: usePageLayout ? 0 : "1.75rem",
                display: "flex",
                justifyContent: usePageLayout ? "flex-start" : "center",
                gap: theme.spacing.md,
            }}>
                {step === "send" && (
                    <>
                        <SecondaryButton onClick={back}>Back</SecondaryButton>
                        <PrimaryButton onClick={handleSendCode} disabled={loading}>
                            {loading ? "Sending..." : "Send code to my email"}
                        </PrimaryButton>
                    </>
                )}

                {step === "verify" && (
                    <>
                        <SecondaryButton onClick={handleResend} disabled={loading}>
                            Resend code
                        </SecondaryButton>
                        <PrimaryButton
                            onClick={handleVerifyCode}
                            disabled={loading || code.length !== 6}
                        >
                            {loading ? "Verifying..." : "Verify"}
                        </PrimaryButton>
                    </>
                )}

                {step === "verified" && (
                    <PrimaryButton onClick={next}>Next</PrimaryButton>
                )}
            </div>
        </>
    );

    if (usePageLayout) {
        return (
            <div
                className="voter-update-registration-page voter-page-content"
                style={getVoterPageContentWrapperStyle(theme)}
            >
                <header>
                    <h1 style={getPageTitleStyle(theme)}>Email Verification</h1>
                </header>
                <section style={getFirstSectionStyle(theme)}>
                    {content}
                </section>
            </div>
        );
    }

    return (
        <div style={{ ...getVoterPageContentWrapperStyle(theme), maxWidth: "100%", margin: "0 auto" }}>
            {content}
        </div>
    );
}

export default EmailCodeVerification;
