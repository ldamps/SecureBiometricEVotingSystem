/**
 * Mobile Biometric Verification Page
 *
 * Accessed by scanning the QR code shown on the desktop voting flow.
 * Re-captures face + ear biometrics, matches against stored templates,
 * decrypts the biometric-bound signing key, signs the server challenge,
 * and submits the signature for verification.
 *
 * Flow:
 *   1. Retrieve stored biometric data (templates + encrypted key) from IndexedDB
 *   2. Capture face + ear via camera
 *   3. Match against stored templates (cosine similarity, AND-fusion)
 *   4. Derive biometric encryption key and decrypt ECDSA private key
 *   5. Sign the server's challenge
 *   6. Submit signature to the server
 */

import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { useTheme } from "../../styles/ThemeContext";
import { getCardStyle, getPageTitleStyle, PrimaryButton } from "../../styles/ui";
import { BiometricApiRepository } from "../../features/voter/repositories/biometric-api.repository";
import BiometricCaptureFlow from "../../features/biometric/components/BiometricCaptureFlow";
import { retrieveBiometricData } from "../../features/biometric/services/biometric-storage.service";
import { matchBoth } from "../../features/biometric/services/biometric-matching.service";
import { decryptPrivateKey } from "../../features/biometric/services/biometric-key-encryption.service";
import { FeatureDescriptor, StoredBiometricData } from "../../features/biometric/models/biometric-feature.model";

const DEVICE_ID_KEY = "evoting_device_id";
const biometricApi = new BiometricApiRepository();

/**
 * Sign a hex-encoded challenge with an ECDSA private key.
 * Returns the signature as a base64 string (matching backend expectation).
 */
async function signChallenge(privateKey: CryptoKey, challengeHex: string): Promise<string> {
  const challengeBytes = new Uint8Array(
    challengeHex.match(/.{1,2}/g)!.map((byte) => parseInt(byte, 16)),
  );
  const signature = await window.crypto.subtle.sign(
    { name: "ECDSA", hash: "SHA-256" },
    privateKey,
    challengeBytes,
  );
  // Base64-encode to match backend's base64.b64decode().
  return btoa(String.fromCharCode.apply(null, Array.from(new Uint8Array(signature))));
}

type VerifyState =
  | "ready"
  | "capturing"
  | "matching"
  | "signing"
  | "submitting"
  | "success"
  | "error"
  | "no_key"
  | "match_failed";

function MobileVerifyPage() {
  const { theme } = useTheme();
  const [searchParams] = useSearchParams();
  const challengeId = searchParams.get("challenge_id");
  const voterId = searchParams.get("voter_id");

  const [state, setState] = useState<VerifyState>("ready");
  const [error, setError] = useState<string | null>(null);
  const [storedData, setStoredData] = useState<StoredBiometricData | null>(null);
  const [matchDetails, setMatchDetails] = useState<string | null>(null);

  // Validate URL parameters.
  useEffect(() => {
    if (!challengeId || !voterId) {
      setError("Missing challenge or voter ID. Please scan the QR code again.");
      setState("error");
    }
  }, [challengeId, voterId]);

  // Load stored biometric data when starting.
  const handleStartVerify = useCallback(async () => {
    if (!voterId) return;
    setError(null);

    const data = await retrieveBiometricData(voterId);
    if (!data) {
      setState("no_key");
      setError(
        "No enrolled device found on this device. " +
        "Please make sure you are using the same device you enrolled with.",
      );
      return;
    }

    setStoredData(data);
    setState("capturing");
  }, [voterId]);

  // After biometric capture completes.
  const handleCaptureComplete = useCallback(
    async (result: { faceDescriptor: FeatureDescriptor; earDescriptor: FeatureDescriptor }) => {
      if (!storedData || !voterId) return;

      try {
        setState("matching");

        // Compare against stored templates.
        const faceRef = new Float32Array(storedData.faceTemplate);
        const earRef = new Float32Array(storedData.earTemplate);
        const matchResult = matchBoth(
          result.faceDescriptor,
          faceRef,
          result.earDescriptor,
          earRef,
        );

        setMatchDetails(
          `Face similarity: ${(matchResult.face.similarity * 100).toFixed(1)}% | ` +
          `Ear similarity: ${(matchResult.ear.similarity * 100).toFixed(1)}%`,
        );

        if (!matchResult.overallPassed) {
          setState("match_failed");
          setError(
            `Biometric match failed. ` +
            `Face: ${(matchResult.face.similarity * 100).toFixed(1)}% (need 60%) | ` +
            `Ear: ${(matchResult.ear.similarity * 100).toFixed(1)}% (need 50%). ` +
            `Please try again.`,
          );
          return;
        }

        // Decrypt the signing key using the biometric-derived encryption key.
        setState("signing");
        let privateKey: CryptoKey;
        try {
          privateKey = await decryptPrivateKey(
            result.faceDescriptor,
            result.earDescriptor,
            storedData.encryptedKeyBundle,
          );
        } catch {
          setState("match_failed");
          setError(
            "Biometric key decryption failed. Your biometric features did not match " +
            "the enrollment closely enough to unlock the signing key. Please try again.",
          );
          return;
        }

        // Request a fresh challenge and sign it.
        setState("submitting");
        const challenge = await biometricApi.createChallenge({ voter_id: voterId });
        const signature = await signChallenge(privateKey, challenge.challenge);

        const deviceId = localStorage.getItem(DEVICE_ID_KEY) || "";
        const verifyResult = await biometricApi.verifyBiometric({
          challenge_id: challenge.id,
          device_id: deviceId,
          signature,
        });

        if (verifyResult.verified) {
          setState("success");
        } else {
          setError(verifyResult.message || "Server rejected the signature.");
          setState("error");
        }
      } catch (err: any) {
        setError(err.message || "Verification failed. Please try again.");
        setState("error");
      }
    },
    [storedData, voterId],
  );

  const handleCaptureError = useCallback((message: string) => {
    setError(message);
    setState("error");
  }, []);

  const messages: Record<VerifyState, string> = {
    ready:
      "Verify your identity using the face and ear biometrics stored on this device. " +
      "Your biometric data never leaves this device \u2014 only a cryptographic " +
      "signature is sent to confirm your identity.",
    capturing: "",
    matching: "Comparing your biometrics against the enrolled templates\u2026",
    signing: "Biometric match successful. Decrypting your signing key\u2026",
    submitting: "Submitting cryptographic proof to the server\u2026",
    success:
      "Identity verified successfully! " +
      "You can now close this page and return to the voting screen. " +
      "It will update automatically.",
    error: "Verification encountered a problem.",
    no_key:
      "No enrollment found on this device. " +
      "Make sure you are using the same phone or tablet you used during registration.",
    match_failed: "Biometric verification failed.",
  };

  return (
    <div
      style={{
        maxWidth: "480px",
        margin: "0 auto",
        padding: "1.5rem 1rem",
        minHeight: "100vh",
      }}
    >
      <h1 style={{ ...getPageTitleStyle(theme), fontSize: "1.4rem", textAlign: "center" }}>
        Biometric Verification
      </h1>

      {/* Status / instructions */}
      {state !== "capturing" && (
        <div style={{ ...getCardStyle(theme), marginTop: "1.25rem" }}>
          <p style={{ color: theme.colors.text.primary, lineHeight: 1.6, fontSize: "0.95rem" }}>
            {messages[state]}
          </p>

          {error && (
            <p style={{ color: theme.colors.status.error, marginTop: theme.spacing.sm }}>
              {error}
            </p>
          )}

          {matchDetails && (state === "success" || state === "match_failed") && (
            <p
              style={{
                color: theme.colors.text.secondary || "#6b7280",
                marginTop: theme.spacing.xs,
                fontSize: "0.85rem",
              }}
            >
              {matchDetails}
            </p>
          )}

          {state === "success" && (
            <div
              style={{
                marginTop: theme.spacing.md,
                padding: theme.spacing.md,
                borderRadius: theme.borderRadius?.md || "8px",
                backgroundColor: "#f0fff4",
                border: `1px solid ${theme.colors.status.success}`,
                textAlign: "center",
              }}
            >
              <strong>Identity verified</strong>
              <p style={{ margin: `${theme.spacing.xs} 0 0 0`, fontSize: "0.9rem" }}>
                Your face and ear confirmed your identity. No biometric data was sent to the server.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Biometric capture flow */}
      {state === "capturing" && (
        <BiometricCaptureFlow
          mode="verify"
          onComplete={handleCaptureComplete}
          onError={handleCaptureError}
        />
      )}

      {/* Action buttons */}
      <div style={{ marginTop: "1.5rem", display: "flex", justifyContent: "center" }}>
        {state === "ready" && (
          <PrimaryButton onClick={handleStartVerify}>Verify Identity</PrimaryButton>
        )}

        {(state === "matching" || state === "signing" || state === "submitting") && (
          <PrimaryButton disabled>Verifying\u2026</PrimaryButton>
        )}

        {(state === "error" || state === "no_key" || state === "match_failed") && (
          <PrimaryButton onClick={handleStartVerify}>Retry</PrimaryButton>
        )}
      </div>
    </div>
  );
}

export default MobileVerifyPage;
