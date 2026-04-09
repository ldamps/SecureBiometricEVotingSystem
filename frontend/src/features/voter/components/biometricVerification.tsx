// Voting Step: Biometric Verification (match-on-device)
// User must be on their phone to use biometric verification.

import { useState, useEffect, useRef, useCallback } from "react";
import { QRCodeSVG } from "qrcode.react";
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
    getSuccessAlertStyle,
} from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";
import { BiometricVerificationStatus } from "../model/biometric.model";
import { BiometricApiRepository } from "../repositories/biometric-api.repository";

const biometricApi = new BiometricApiRepository();

/**
 * Detect whether the current device supports biometric capture directly
 * (phones, tablets, iPads).
 */
function isMobileOrTablet(): boolean {
    if (typeof window === "undefined") return false;
    const hasTouchScreen = "ontouchstart" in window || navigator.maxTouchPoints > 0;
    const ua = navigator.userAgent || "";
    const mobileTabletUA = /Android|iPhone|iPad|iPod|webOS|BlackBerry|IEMobile|Opera Mini|Tablet|Silk/i.test(ua);
    return hasTouchScreen && mobileTabletUA;
}

const POLL_INTERVAL = 2000;
const POLL_TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes

function BiometricVerification({
    next,
    state,
    setState,
    progressStep = 2,
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
    const isMobile = isMobileOrTablet();

    const handleStartVerification = useCallback(async () => {
        setError(null);
        setStatus(BiometricVerificationStatus.CHALLENGE_ISSUED);

        try {
            const challenge = await biometricApi.createChallenge({
                voter_id: state.voterId,
            });
            setChallengeId(challenge.id);
            setChallengeHex(challenge.challenge);

            if (isMobile) {
                // On mobile/tablet — navigate directly to the verification page
                const verifyUrl = `${window.location.origin}/biometric/verify?challenge_id=${encodeURIComponent(challenge.id)}&voter_id=${encodeURIComponent(state.voterId)}`;
                window.location.href = verifyUrl;
                return;
            }

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
            const pollStarted = Date.now();

            pollRef.current = setInterval(async () => {
                // Timeout — stop polling after 5 minutes
                if (Date.now() - pollStarted > POLL_TIMEOUT_MS) {
                    if (pollRef.current) clearInterval(pollRef.current);
                    setError("Verification timed out. Please try again.");
                    setStatus(BiometricVerificationStatus.FAILED);
                    return;
                }
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
    }, [state, setState, isMobile]);

    const handleCancel = () => {
        if (pollRef.current) clearInterval(pollRef.current);
        setStatus(BiometricVerificationStatus.IDLE);
        setChallengeId(null);
        setChallengeHex(null);
    };

    const statusMessages: Record<BiometricVerificationStatus, string> = {
        [BiometricVerificationStatus.IDLE]:
            "Before casting your vote, we need to verify your identity using " +
            "the face and ear biometrics stored on your mobile device. " +
            "Please have your enrolled phone ready \u2014 you will need to scan " +
            "a QR code with it. Your biometric data never leaves your phone.",
        [BiometricVerificationStatus.CHALLENGE_ISSUED]:
            "Preparing verification challenge\u2026",
        [BiometricVerificationStatus.AWAITING_DEVICE]:
            "Open the camera on the phone you enrolled with and scan the QR code below. " +
            "Your phone will ask you to verify your face and ear. " +
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
                            backgroundColor: "#ffffff",
                            padding: "12px",
                        }}>
                            <QRCodeSVG
                                value={`${window.location.origin}/biometric/verify?challenge_id=${encodeURIComponent(challengeId)}&voter_id=${encodeURIComponent(state.voterId)}`}
                                size={196}
                                level="M"
                            />
                        </div>

                        <p style={{
                            marginTop: theme.spacing.sm,
                            fontSize: "0.85rem",
                            color: theme.colors.text.secondary,
                            textAlign: "center",
                            maxWidth: "320px",
                        }}>
                            Open the <strong>E-Voting Authenticator</strong> app on your phone and scan this code.
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
                        ...getSuccessAlertStyle(theme),
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

                {/* Dev-only: skip biometric verification when testing locally.
                    Guarded by both NODE_ENV and an explicit env flag to prevent
                    accidental exposure in production. */}
                {process.env.NODE_ENV === "development" && process.env.REACT_APP_ALLOW_BIOMETRIC_SKIP === "true" && status !== BiometricVerificationStatus.VERIFIED && (
                    <SecondaryButton onClick={() => {
                        setState({ ...state, biometricVerified: true });
                        setStatus(BiometricVerificationStatus.VERIFIED);
                    }}>
                        Skip (dev only)
                    </SecondaryButton>
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
