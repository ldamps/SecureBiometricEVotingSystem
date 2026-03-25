import { useState, useEffect, useRef, useCallback } from "react";
import { PrimaryButton, SecondaryButton, getCardStyle, getStepTitleStyle, getStepDescStyle, getFirstSectionStyle, getPageTitleStyle, getVoterPageContentWrapperStyle } from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";
import ProgressBar from "./progressBar";
import { BiometricEnrollmentStatus } from "../model/biometric.model";
import { BiometricApiRepository } from "../repositories/biometric-api.repository";

const biometricApi = new BiometricApiRepository();

/** Interval (ms) at which the laptop polls for enrollment completion. */
const POLL_INTERVAL = 3000;

function BiometricRegistration({
    next,
    back,
    state,
    setState,
    progressStep = 4,
    heading = "Registration: Register Your Biometrics",
    showProgressBar = true,
    primaryButtonLabel = "Next",
    usePageLayout = false,
}: {
    next: () => void;
    back: () => void;
    state: any;
    setState: (state: any) => void;
    progressStep?: number;
    heading?: string;
    showProgressBar?: boolean;
    primaryButtonLabel?: string;
    usePageLayout?: boolean;
}) {
    const { theme } = useTheme();
    const [enrollmentStatus, setEnrollmentStatus] = useState<BiometricEnrollmentStatus>(
        state.biometricEnrolled
            ? BiometricEnrollmentStatus.ENROLLED
            : BiometricEnrollmentStatus.NOT_STARTED
    );
    const [error, setError] = useState<string | null>(null);
    const [qrPayload, setQrPayload] = useState<string | null>(null);
    const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

    // Stop polling on unmount or when enrolled
    useEffect(() => {
        return () => {
            if (pollRef.current) clearInterval(pollRef.current);
        };
    }, []);

    /**
     * Poll the server to detect when the mobile device has completed
     * enrollment.  Once an active credential for this voter appears,
     * transition to ENROLLED.
     */
    const startPolling = useCallback(() => {
        if (pollRef.current) clearInterval(pollRef.current);

        pollRef.current = setInterval(async () => {
            try {
                const credentials = await biometricApi.listCredentials(state.voterId);
                const active = credentials.find((c) => c.is_active);
                if (active) {
                    if (pollRef.current) clearInterval(pollRef.current);
                    setState({
                        ...state,
                        biometricEnrolled: true,
                        credentialId: active.id,
                        deviceId: active.device_id,
                    });
                    setEnrollmentStatus(BiometricEnrollmentStatus.ENROLLED);
                }
            } catch {
                // Polling failure is non-fatal — we just retry next tick.
            }
        }, POLL_INTERVAL);
    }, [state, setState]);

    /**
     * Generate the QR code payload and start polling.
     *
     * The QR code encodes a deep-link URL that the mobile voting app
     * can open to begin on-device biometric enrollment.  The URL
     * includes the voter_id so the phone knows which voter to enrol for.
     *
     * Example deep link:  evoting://enroll?voter_id=<uuid>
     */
    const handleStartEnrollment = () => {
        setError(null);
        const deepLink = `evoting://enroll?voter_id=${encodeURIComponent(state.voterId)}`;
        setQrPayload(deepLink);
        setEnrollmentStatus(BiometricEnrollmentStatus.WAITING_FOR_DEVICE);
        startPolling();
    };

    const handleCancel = () => {
        if (pollRef.current) clearInterval(pollRef.current);
        setEnrollmentStatus(BiometricEnrollmentStatus.NOT_STARTED);
        setQrPayload(null);
    };

    const statusMessages: Record<BiometricEnrollmentStatus, string> = {
        [BiometricEnrollmentStatus.NOT_STARTED]:
            "To secure your vote, we need to link your mobile device. " +
            "Your face and ear biometrics will be stored only on your phone \u2014 " +
            "they are never sent to our servers.",
        [BiometricEnrollmentStatus.WAITING_FOR_DEVICE]:
            "Scan the QR code below with your mobile voting app. " +
            "The app will guide you through capturing your face and ear biometrics. " +
            "This page will update automatically once your device completes enrollment.",
        [BiometricEnrollmentStatus.CAPTURING]:
            "Your device is capturing your face and ear biometrics. " +
            "Please follow the instructions on your phone.",
        [BiometricEnrollmentStatus.ENROLLING]:
            "Registering your device with the voting platform\u2026",
        [BiometricEnrollmentStatus.ENROLLED]:
            "Your device has been successfully enrolled. Your biometric data " +
            "is stored securely on your phone and will never leave your device.",
        [BiometricEnrollmentStatus.ERROR]:
            "Something went wrong during enrollment. Please try again.",
    };

    const content = (
        <>
            {!usePageLayout && (
                <div style={{ ...getCardStyle(theme), marginBottom: "1.75rem" }}>
                    {showProgressBar && <ProgressBar step={progressStep} theme={theme} />}
                    <h1 style={getStepTitleStyle(theme)}>{heading}</h1>
                </div>
            )}

            {/* Status message */}
            <div style={{ ...getCardStyle(theme), marginBottom: "1.25rem" }}>
                <p style={getStepDescStyle(theme)}>
                    {statusMessages[enrollmentStatus]}
                </p>

                {error && (
                    <p style={{ color: theme.colors.status.error, marginTop: theme.spacing.sm }}>
                        {error}
                    </p>
                )}

                {/* QR code — shown when waiting for the mobile device */}
                {enrollmentStatus === BiometricEnrollmentStatus.WAITING_FOR_DEVICE && qrPayload && (
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
                            {/* TODO: render a real QR code here for production
                              In production, render a real QR code here using a
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
                                    marginBottom: "8px",
                                }}>
                                    <span style={{ fontSize: "0.75rem", color: theme.colors.text.secondary, wordBreak: "break-all", padding: "4px" }}>
                                        QR: {qrPayload}
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
                            Your biometrics (face + ear) will be captured and stored
                            only on your device.
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

                {/* Enrolled confirmation */}
                {enrollmentStatus === BiometricEnrollmentStatus.ENROLLED && (
                    <div style={{
                        marginTop: theme.spacing.md,
                        padding: theme.spacing.md,
                        borderRadius: theme.borderRadius?.md || "8px",
                        backgroundColor: "#f0fff4",
                        border: `1px solid ${theme.colors.status.success}`,
                    }}>
                        <strong>Device enrolled</strong>
                        <p style={{ margin: `${theme.spacing.xs} 0 0 0`, fontSize: "0.9rem" }}>
                            Biometric modalities: face + ear (stored on device only)
                        </p>
                        <p style={{ margin: `${theme.spacing.xs} 0 0 0`, fontSize: "0.85rem", color: theme.colors.text.secondary }}>
                            The server holds only your device&apos;s public key &mdash; no biometric data.
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
                <SecondaryButton onClick={back}>Back</SecondaryButton>

                {enrollmentStatus === BiometricEnrollmentStatus.NOT_STARTED && (
                    <PrimaryButton onClick={handleStartEnrollment}>
                        Link Mobile Device
                    </PrimaryButton>
                )}

                {enrollmentStatus === BiometricEnrollmentStatus.WAITING_FOR_DEVICE && (
                    <SecondaryButton onClick={handleCancel}>
                        Cancel
                    </SecondaryButton>
                )}

                {enrollmentStatus === BiometricEnrollmentStatus.ERROR && (
                    <PrimaryButton onClick={handleStartEnrollment}>
                        Retry
                    </PrimaryButton>
                )}

                {enrollmentStatus === BiometricEnrollmentStatus.ENROLLED && (
                    <PrimaryButton onClick={next}>{primaryButtonLabel}</PrimaryButton>
                )}
            </div>
        </>
    );

    if (usePageLayout) {
        return (
            <div className="voter-update-registration-page voter-page-content" style={getVoterPageContentWrapperStyle(theme)}>
                <header>
                    <h1 style={getPageTitleStyle(theme)}>{heading}</h1>
                </header>
                <section style={getFirstSectionStyle(theme)}>
                    {content}
                </section>
            </div>
        );
    }

    return <div>{content}</div>;
}

export default BiometricRegistration;