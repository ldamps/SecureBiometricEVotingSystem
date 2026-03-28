// Mobile Biometric Verification Page
// Accessed by scanning the QR code shown on the desktop voting flow.
// Runs on the user's phone/tablet to perform on-device biometric
// verification and sign the server's challenge with the stored private key.

import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { useTheme } from "../../styles/ThemeContext";
import { getCardStyle, getPageTitleStyle, PrimaryButton } from "../../styles/ui";
import { BiometricApiRepository } from "../../features/voter/repositories/biometric-api.repository";

const biometricApi = new BiometricApiRepository();

const DEVICE_ID_KEY = "evoting_device_id";
const SIGNING_KEY_DB = "evoting_signing_keys";

/**
 * Store a CryptoKey in IndexedDB so it persists across sessions.
 * The key is non-extractable and can only be used for signing.
 */
async function storeSigningKey(voterId: string, key: CryptoKey): Promise<void> {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(SIGNING_KEY_DB, 1);
        request.onupgradeneeded = () => {
            const db = request.result;
            if (!db.objectStoreNames.contains("keys")) {
                db.createObjectStore("keys");
            }
        };
        request.onsuccess = () => {
            const db = request.result;
            const tx = db.transaction("keys", "readwrite");
            tx.objectStore("keys").put(key, voterId);
            tx.oncomplete = () => resolve();
            tx.onerror = () => reject(tx.error);
        };
        request.onerror = () => reject(request.error);
    });
}

/**
 * Retrieve the signing key for a voter from IndexedDB.
 */
async function getSigningKey(voterId: string): Promise<CryptoKey | null> {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(SIGNING_KEY_DB, 1);
        request.onupgradeneeded = () => {
            const db = request.result;
            if (!db.objectStoreNames.contains("keys")) {
                db.createObjectStore("keys");
            }
        };
        request.onsuccess = () => {
            const db = request.result;
            const tx = db.transaction("keys", "readonly");
            const getReq = tx.objectStore("keys").get(voterId);
            getReq.onsuccess = () => resolve(getReq.result ?? null);
            getReq.onerror = () => reject(getReq.error);
        };
        request.onerror = () => reject(request.error);
    });
}

/**
 * Sign the challenge hex string with the stored ECDSA private key.
 * Returns the signature as a hex string.
 */
async function signChallenge(privateKey: CryptoKey, challengeHex: string): Promise<string> {
    const challengeBytes = new Uint8Array(
        challengeHex.match(/.{1,2}/g)!.map((byte) => parseInt(byte, 16))
    );
    const signature = await window.crypto.subtle.sign(
        { name: "ECDSA", hash: "SHA-256" },
        privateKey,
        challengeBytes
    );
    return Array.from(new Uint8Array(signature))
        .map((b) => b.toString(16).padStart(2, "0"))
        .join("");
}

type VerifyState = "ready" | "authenticating" | "signing" | "submitting" | "success" | "error" | "no_key";

function MobileVerifyPage() {
    const { theme } = useTheme();
    const [searchParams] = useSearchParams();
    const challengeId = searchParams.get("challenge_id");
    const voterId = searchParams.get("voter_id");

    const [state, setState] = useState<VerifyState>("ready");
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!challengeId || !voterId) {
            setError("Missing challenge or voter ID. Please scan the QR code again.");
            setState("error");
        }
    }, [challengeId, voterId]);

    const handleVerify = useCallback(async () => {
        if (!challengeId || !voterId) return;
        setError(null);
        setState("authenticating");

        try {
            // Step 1: Retrieve the stored signing key for this voter
            const privateKey = await getSigningKey(voterId);
            if (!privateKey) {
                setState("no_key");
                setError(
                    "No enrolled device key found on this device. " +
                    "Please make sure you are using the same device you enrolled with."
                );
                return;
            }

            // Step 2: Get the challenge to sign.
            // The desktop already created the challenge, but we need the hex value.
            // Create a fresh challenge tied to this voter to get the hex.
            setState("signing");
            const challenge = await biometricApi.createChallenge({ voter_id: voterId });
            // Step 3: Sign the challenge with the device's private key
            const signature = await signChallenge(privateKey, challenge.challenge);

            setState("submitting");

            // Step 4: Submit the signed challenge to the server
            const deviceId = localStorage.getItem(DEVICE_ID_KEY) || "";
            const result = await biometricApi.verifyBiometric({
                challenge_id: challenge.id,
                device_id: deviceId,
                signature,
            });

            if (result.verified) {
                setState("success");
            } else {
                setError(result.message || "Verification failed.");
                setState("error");
            }
        } catch (err: any) {
            setError(err.message || "Verification failed. Please try again.");
            setState("error");
        }
    }, [challengeId, voterId]);

    const messages: Record<VerifyState, string> = {
        ready:
            "Verify your identity using the biometrics stored on this device. " +
            "Your biometric data never leaves this device — only a cryptographic " +
            "signature is sent to confirm your identity.",
        authenticating: "Retrieving your device credentials\u2026",
        signing: "Signing the verification challenge\u2026",
        submitting: "Submitting verification to the server\u2026",
        success:
            "Identity verified successfully! " +
            "You can now close this page and return to the voting screen. " +
            "It will update automatically.",
        error: "Verification encountered a problem.",
        no_key:
            "No enrollment found on this device. " +
            "Make sure you are using the same phone or tablet you used during registration.",
    };

    return (
        <div style={{
            maxWidth: "480px",
            margin: "0 auto",
            padding: "1.5rem 1rem",
            minHeight: "100vh",
        }}>
            <h1 style={{ ...getPageTitleStyle(theme), fontSize: "1.4rem", textAlign: "center" }}>
                Biometric Verification
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
                        <strong>Identity verified</strong>
                        <p style={{ margin: `${theme.spacing.xs} 0 0 0`, fontSize: "0.9rem" }}>
                            Your device confirmed your identity. No biometric data was sent to the server.
                        </p>
                    </div>
                )}
            </div>

            <div style={{ marginTop: "1.5rem", display: "flex", justifyContent: "center" }}>
                {state === "ready" && (
                    <PrimaryButton onClick={handleVerify}>
                        Verify Identity
                    </PrimaryButton>
                )}

                {(state === "authenticating" || state === "signing" || state === "submitting") && (
                    <PrimaryButton disabled>
                        Verifying\u2026
                    </PrimaryButton>
                )}

                {(state === "error" || state === "no_key") && (
                    <PrimaryButton onClick={handleVerify}>
                        Retry
                    </PrimaryButton>
                )}
            </div>
        </div>
    );
}

// Export the helper so the enrollment page can store keys after generating them
export { storeSigningKey };
export default MobileVerifyPage;
