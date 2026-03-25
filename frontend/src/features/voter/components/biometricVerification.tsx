// Voting Step: Biometric Verification (match-on-device)
// User must be on their phone to use biometric verification.

import { useState, useEffect, useRef, useCallback } from "react";
import ProgressBar from "./progressBar";
import {
    getVoterPageContentWrapperStyle,
    getCardStyle,
    getStepTitleStyle,
    getStepDescStyle,
    getFirstSectionStyle,
    getPageTitleStyle,
    PrimaryButton,
    SecondaryButton,
} from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";
import { BiometricVerificationStatus } from "../model/biometric.model";
import { BiometricApiRepository } from "../repositories/biometric-api.repository";

const biometricApi = new BiometricApiRepository();

const POLL_INTERVAL = 2000;

function BiometricVerification({
    next,
    state,
    setState,
    progressStep = 3,
    showProgressBar = true,
    usePageLayout = false,
}: {
    next: () => void;
    state: any;
    setState: (state: any) => void;
    progressStep?: number;
    showProgressBar?: boolean;
    usePageLayout?: boolean;
}) {
    const { theme } = useTheme();
    const [status, setStatus] = useState<BiometricVerificationStatus>(
        BiometricVerificationStatus.IDLE
    );
    const [challengeId, setChallengeId] = useState<string | null>(null);
    const [challengeHex, setChallengeHex] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

    useEffect(() => {
        return () => {
            if (pollRef.current) clearInterval(pollRef.current);
        };
    }, []);

    /**
     * Request a challenge from the server, then show a QR code for the
     * phone to scan.  The phone will:
     *   1. Perform face + ear biometric match on-device.
     *   2. Sign the challenge with the enrolled private key.
     *   3. POST the signature to /biometric/verify.
     *
     * Meanwhile we poll /biometric/verify indirectly: we re-issue a
     * verification check.  In a production system, this would use a
     * WebSocket or SSE push, but polling works for the MVP.
     */
    const handleStartVerification = useCallback(async () => {
        setError(null);
        setStatus(BiometricVerificationStatus.CHALLENGE_ISSUED);

        try {
            const challenge = await biometricApi.createChallenge({
                voter_id: state.voterId,
            });
            setChallengeId(challenge.id);
            setChallengeHex(challenge.challenge);
            setStatus(BiometricVerificationStatus.AWAITING_DEVICE);

            // Start polling — the mobile app will call POST /biometric/verify
            // once the on-device match succeeds.  We detect success by
            // observing the challenge is consumed (the verify endpoint is
            // called by the phone, not by us).
            //
            // A lightweight approach: we try to verify with a dummy signature
            // and check the error message.  A proper implementation would use
            // a dedicated "challenge status" endpoint or WebSocket.  For now
            // we simply poll the credentials endpoint to check last_used_at
            // changed — indicating the phone completed verification.
            if (pollRef.current) clearInterval(pollRef.current);
            const credentialsBefore = await biometricApi.listCredentials(state.voterId);
            const activeBefore = credentialsBefore.find((c) => c.is_active);
            const lastUsedBefore = activeBefore?.last_used_at;

            pollRef.current = setInterval(async () => {
                try {
                    const credentials = await biometricApi.listCredentials(state.voterId);
                    const active = credentials.find((c) => c.is_active);
                    if (active && active.last_used_at && active.last_used_at !== lastUsedBefore) {
                        // The phone successfully verified — credential was touched
                        if (pollRef.current) clearInterval(pollRef.current);
                        setState({ ...state, biometricVerified: true });
                        setStatus(BiometricVerificationStatus.VERIFIED);
                    }
                } catch {
                    // Non-fatal polling error
                }
            }, POLL_INTERVAL);
        } catch (err: any) {
            setError(err.message || "Failed to create verification challenge.");
            setStatus(BiometricVerificationStatus.FAILED);
        }
    }, [state, setState]);

    const handleCancel = () => {
        if (pollRef.current) clearInterval(pollRef.current);
        setStatus(BiometricVerificationStatus.IDLE);
        setChallengeId(null);
        setChallengeHex(null);
    };

    const statusMessages: Record<BiometricVerificationStatus, string> = {
        [BiometricVerificationStatus.IDLE]:
            "Before casting your vote, we need to verify your identity using " +
            "the biometrics stored on your mobile device. Your biometric data " +
            "never leaves your phone.",
        [BiometricVerificationStatus.CHALLENGE_ISSUED]:
            "Preparing verification challenge\u2026",
        [BiometricVerificationStatus.AWAITING_DEVICE]:
            "Scan the QR code below with your mobile voting app. " +
            "The app will ask you to verify your face and ear. " +
            "This page will update automatically once verification is complete.",
        [BiometricVerificationStatus.VERIFYING]:
            "Verifying your identity\u2026",
        [BiometricVerificationStatus.VERIFIED]:
            "Identity verified successfully. You may now proceed to cast your vote.",
        [BiometricVerificationStatus.FAILED]:
            "Verification failed. Please try again.",
    };

    const content = (
        <>
            {!usePageLayout && (
                <>
                    {showProgressBar && (
                        <div style={{ ...getCardStyle(theme), marginBottom: "1.75rem" }}>
                            <ProgressBar step={progressStep} theme={theme} />
                        </div>
                    )}
                    <h1 style={getStepTitleStyle(theme)}>Biometric Verification</h1>
                </>
            )}

            <div style={{ ...getCardStyle(theme), marginBottom: "1.25rem" }}>
                <p style={getStepDescStyle(theme)}>
                    {statusMessages[status]}
                </p>

                {error && (
                    <p style={{ color: theme.colors.status.error, marginTop: theme.spacing.sm }}>
                        {error}
                    </p>
                )}

                {/* QR code for the phone to scan */}
                {status === BiometricVerificationStatus.AWAITING_DEVICE && challengeId && challengeHex && (
                    <div style={{
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        margin: `${theme.spacing.lg} 0`,
                    }}>
                        <div style={{
                            width: "220px",
                            height: "220px",
                            border: `2px solid ${theme.colors.border || "#ccc"}`,
                            borderRadius: theme.borderRadius?.md || "8px",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            backgroundColor: theme.colors.surface || "#ffffff",
                            padding: "12px",
                        }}>
                            {/*
                              In production, render a real QR code:
                              <QRCodeSVG value={qrPayload} size={196} />
                            */}
                            <div style={{ textAlign: "center" }}>
                                <div style={{
                                    width: "160px",
                                    height: "160px",
                                    backgroundColor: theme.colors.background || "#f5f5f5",
                                    border: `1px dashed ${theme.colors.border || "#ccc"}`,
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                }}>
                                    <span style={{ fontSize: "0.7rem", color: theme.colors.text.secondary, wordBreak: "break-all", padding: "4px" }}>
                                        QR: evoting://verify?challenge_id={challengeId}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <p style={{
                            marginTop: theme.spacing.sm,
                            fontSize: "0.85rem",
                            color: theme.colors.text.secondary,
                            textAlign: "center",
                            maxWidth: "320px",
                        }}>
                            Open the voting app on your phone and scan this code.
                            Complete the face + ear check on your device.
                        </p>

                        <p style={{
                            marginTop: theme.spacing.xs,
                            fontSize: "0.8rem",
                            color: theme.colors.text.secondary,
                        }}>
                            Waiting for your device\u2026
                        </p>
                    </div>
                )}

                {/* Verified confirmation */}
                {status === BiometricVerificationStatus.VERIFIED && (
                    <div style={{
                        marginTop: theme.spacing.md,
                        padding: theme.spacing.md,
                        borderRadius: theme.borderRadius?.md || "8px",
                        backgroundColor: "#f0fff4",
                        border: `1px solid ${theme.colors.status.success}`,
                    }}>
                        <strong>Identity verified</strong>
                        <p style={{ margin: `${theme.spacing.xs} 0 0 0`, fontSize: "0.9rem" }}>
                            Your device confirmed your identity using face + ear biometrics.
                            No biometric data was sent to the server.
                        </p>
                    </div>
                )}
            </div>

            {/* Action buttons */}
            <div style={{
                marginTop: usePageLayout ? 0 : "1.75rem",
                display: "flex",
                justifyContent: usePageLayout ? "flex-start" : "center",
                gap: theme.spacing.md,
            }}>
                {status === BiometricVerificationStatus.IDLE && (
                    <PrimaryButton onClick={handleStartVerification}>
                        Verify Identity
                    </PrimaryButton>
                )}

                {status === BiometricVerificationStatus.AWAITING_DEVICE && (
                    <SecondaryButton onClick={handleCancel}>
                        Cancel
                    </SecondaryButton>
                )}

                {status === BiometricVerificationStatus.FAILED && (
                    <PrimaryButton onClick={handleStartVerification}>
                        Retry
                    </PrimaryButton>
                )}

                {status === BiometricVerificationStatus.VERIFIED && (
                    <PrimaryButton onClick={next}>Next</PrimaryButton>
                )}
            </div>
        </>
    );

    if (usePageLayout) {
        return (
            <div className="voter-update-registration-page voter-page-content" style={getVoterPageContentWrapperStyle(theme)}>
                <header>
                    <h1 style={getPageTitleStyle(theme)}>Biometric Verification</h1>
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

export default BiometricVerification;
