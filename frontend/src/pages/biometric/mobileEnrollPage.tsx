// Mobile Biometric Enrollment Page
// Accessed by scanning the QR code shown on the desktop registration flow.
// Runs on the user's phone/tablet to capture face + ear biometrics
// and register the device's public key with the server.

import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { useTheme } from "../../styles/ThemeContext";
import { getCardStyle, getPageTitleStyle, PrimaryButton } from "../../styles/ui";
import { BiometricApiRepository } from "../../features/voter/repositories/biometric-api.repository";
import { storeSigningKey } from "./mobileVerifyPage";

const biometricApi = new BiometricApiRepository();

/**
 * Generate an ECDSA P-256 key pair using the Web Crypto API.
 * The private key is non-extractable and stored in the browser's key store.
 * Returns the public key in PEM format for server-side storage.
 */
async function generateKeyPair(): Promise<{ publicKeyPem: string; privateKey: CryptoKey }> {
    const keyPair = await window.crypto.subtle.generateKey(
        { name: "ECDSA", namedCurve: "P-256" },
        false,  // private key is NOT extractable
        ["sign", "verify"]
    );

    const publicKeyDer = await window.crypto.subtle.exportKey("spki", keyPair.publicKey);
    const publicKeyBase64 = btoa(String.fromCharCode.apply(null, Array.from(new Uint8Array(publicKeyDer))));
    const publicKeyPem = `-----BEGIN PUBLIC KEY-----\n${publicKeyBase64.match(/.{1,64}/g)!.join("\n")}\n-----END PUBLIC KEY-----`;

    return { publicKeyPem, privateKey: keyPair.privateKey };
}

/**
 * Generate a stable device ID from this browser/device.
 * Uses a fingerprint stored in localStorage so the same device
 * produces the same ID across sessions.
 */
function getOrCreateDeviceId(): string {
    const STORAGE_KEY = "evoting_device_id";
    let deviceId = localStorage.getItem(STORAGE_KEY);
    if (!deviceId) {
        deviceId = crypto.randomUUID();
        localStorage.setItem(STORAGE_KEY, deviceId);
    }
    return deviceId;
}

type EnrollState = "ready" | "authenticating" | "enrolling" | "success" | "error";

function MobileEnrollPage() {
    const { theme } = useTheme();
    const [searchParams] = useSearchParams();
    const voterId = searchParams.get("voter_id");

    const [state, setState] = useState<EnrollState>("ready");
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!voterId) {
            setError("Missing voter ID. Please scan the QR code again from the registration page.");
            setState("error");
        }
    }, [voterId]);

    const handleEnroll = useCallback(async () => {
        if (!voterId) return;
        setError(null);
        setState("authenticating");

        try {
            // Step 1: Generate ECDSA P-256 key pair
            const { publicKeyPem, privateKey } = await generateKeyPair();
            const deviceId = getOrCreateDeviceId();

            // Store the private key in IndexedDB for future verification
            await storeSigningKey(voterId, privateKey);

            setState("enrolling");

            // Step 2: Register the public key with the server
            await biometricApi.enrollDevice({
                voter_id: voterId,
                public_key_pem: publicKeyPem,
                device_id: deviceId,
                modalities: "face+ear",
                device_label: navigator.userAgent.slice(0, 100),
            });

            setState("success");
        } catch (err: any) {
            setError(err.message || "Enrollment failed. Please try again.");
            setState("error");
        }
    }, [voterId]);

    const messages: Record<EnrollState, string> = {
        ready:
            "This device will be linked to your voter account. " +
            "Your biometric data (face + ear) will be captured and stored only on this device — " +
            "the server will only receive a cryptographic public key.",
        authenticating: "Generating secure keys on your device\u2026",
        enrolling: "Registering your device with the voting platform\u2026",
        success:
            "Your device has been successfully enrolled! " +
            "You can now close this page and return to the registration screen on your computer. " +
            "It will update automatically.",
        error: "Something went wrong during enrollment.",
    };

    return (
        <div style={{
            maxWidth: "480px",
            margin: "0 auto",
            padding: "1.5rem 1rem",
            minHeight: "100vh",
        }}>
            <h1 style={{ ...getPageTitleStyle(theme), fontSize: "1.4rem", textAlign: "center" }}>
                Biometric Enrollment
            </h1>

            <div style={{ ...getCardStyle(theme), marginTop: "1.25rem" }}>
                <p style={{ color: theme.colors.text.primary, lineHeight: 1.6, fontSize: "0.95rem" }}>
                    {messages[state]}
                </p>

                {error && (
                    <p style={{ color: theme.colors.status.error, marginTop: theme.spacing.sm }}>
                        {error}
                    </p>
                )}

                {state === "success" && (
                    <div style={{
                        marginTop: theme.spacing.md,
                        padding: theme.spacing.md,
                        borderRadius: theme.borderRadius?.md || "8px",
                        backgroundColor: "#f0fff4",
                        border: `1px solid ${theme.colors.status.success}`,
                        textAlign: "center",
                    }}>
                        <strong>Device enrolled</strong>
                        <p style={{ margin: `${theme.spacing.xs} 0 0 0`, fontSize: "0.9rem" }}>
                            Biometric modalities: face + ear (stored on device only)
                        </p>
                    </div>
                )}
            </div>

            <div style={{ marginTop: "1.5rem", display: "flex", justifyContent: "center" }}>
                {state === "ready" && (
                    <PrimaryButton onClick={handleEnroll}>
                        Start Enrollment
                    </PrimaryButton>
                )}

                {(state === "authenticating" || state === "enrolling") && (
                    <PrimaryButton disabled>
                        {state === "authenticating" ? "Generating keys\u2026" : "Enrolling\u2026"}
                    </PrimaryButton>
                )}

                {state === "error" && (
                    <PrimaryButton onClick={handleEnroll}>
                        Retry
                    </PrimaryButton>
                )}
            </div>
        </div>
    );
}

export default MobileEnrollPage;
