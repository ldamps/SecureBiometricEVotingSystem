/**
 * Authenticator PWA — Biometric Verification
 *
 * Identical logic to mobileVerifyPage.tsx but without PWA redirect
 * bookkeeping.  After success/error a "Back to Scanner" button
 * returns to /auth.
 */

import { useState, useEffect, useCallback } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useTheme } from "../../styles/ThemeContext";
import { getCardStyle, getSuccessAlertStyle, PrimaryButton, SecondaryButton } from "../../styles/ui";
import { BiometricApiRepository } from "../../features/voter/repositories/biometric-api.repository";
import BiometricCaptureFlow from "../../features/biometric/components/BiometricCaptureFlow";
import { decryptPrivateKey } from "../../features/biometric/services/biometric-key-encryption.service";
import { matchBoth } from "../../features/biometric/services/biometric-matching.service";
import { retrieveBiometricData, getDeviceId } from "../../features/biometric/services/biometric-storage.service";
import { FeatureDescriptor, EncryptedKeyBundle } from "../../features/biometric/models/biometric-feature.model";
import PwaInstallGate from "../../features/biometric/components/PwaInstallGate";

const biometricApi = new BiometricApiRepository();

async function signChallenge(privateKey: CryptoKey, challengeHex: string): Promise<string> {
  const challengeBytes = new Uint8Array(
    challengeHex.match(/.{1,2}/g)!.map((byte) => parseInt(byte, 16)),
  );
  const signature = await window.crypto.subtle.sign(
    { name: "ECDSA", hash: "SHA-256" },
    privateKey,
    challengeBytes,
  );
  return btoa(String.fromCharCode.apply(null, Array.from(new Uint8Array(signature))));
}

type VerifyState =
  | "ready" | "loading" | "capturing" | "decrypting"
  | "submitting" | "success" | "error" | "no_enrollment" | "decrypt_failed";

function AuthVerifyPage() {
  const { theme } = useTheme();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const challengeId = searchParams.get("challenge_id");
  const voterId = searchParams.get("voter_id");

  const [state, setState] = useState<VerifyState>("ready");
  const [error, setError] = useState<string | null>(null);
  const [encryptedBundle, setEncryptedBundle] = useState<EncryptedKeyBundle | null>(null);
  const [enrolledDeviceId, setEnrolledDeviceId] = useState<string>("");
  const [enrolledFace, setEnrolledFace] = useState<FeatureDescriptor | null>(null);
  const [enrolledEar, setEnrolledEar] = useState<FeatureDescriptor | null>(null);

  useEffect(() => {
    if (!challengeId || !voterId) {
      setError("Missing challenge or voter ID. Go back and scan the QR code again.");
      setState("error");
    }
  }, [challengeId, voterId]);

  const handleStartVerify = useCallback(async () => {
    if (!voterId) return;
    setError(null);
    setState("loading");

    try {
      const credentials = await biometricApi.listCredentials(voterId);
      const active = credentials.find((c) => c.is_active && c.encrypted_key_bundle);

      if (!active || !active.encrypted_key_bundle) {
        setState("no_enrollment");
        setError("No biometric enrollment found. Please complete enrollment first.");
        return;
      }

      const localDeviceId = await getDeviceId();
      setEnrolledDeviceId(localDeviceId || active.device_id);

      const stored = await retrieveBiometricData(voterId);
      if (stored?.faceTemplate && stored?.earTemplate) {
        setEnrolledFace(new Float32Array(stored.faceTemplate));
        setEnrolledEar(new Float32Array(stored.earTemplate));
      } else {
        setEnrolledFace(null);
        setEnrolledEar(null);
      }

      setEncryptedBundle(JSON.parse(active.encrypted_key_bundle));
      setState("capturing");
    } catch (err: any) {
      setError(err.message || "Failed to fetch enrollment data.");
      setState("error");
    }
  }, [voterId]);

  const handleCaptureComplete = useCallback(
    async (result: { faceDescriptor: FeatureDescriptor; earDescriptor: FeatureDescriptor }) => {
      if (!encryptedBundle || !voterId) return;

      try {
        setState("decrypting");

        // Advisory template matching — does NOT block key decryption.
        let templateMatchFailed = false;
        if (enrolledFace && enrolledEar) {
          const match = matchBoth(
            result.faceDescriptor, enrolledFace,
            result.earDescriptor, enrolledEar,
          );
          templateMatchFailed = !match.overallPassed;
        }

        // Primary security gate: biometric key decryption (AES-GCM).
        let privateKey: CryptoKey;
        try {
          privateKey = await decryptPrivateKey(
            result.faceDescriptor,
            result.earDescriptor,
            encryptedBundle,
          );
        } catch {
          setState("decrypt_failed");
          setError(
            templateMatchFailed
              ? "Biometric verification failed. Your face and ear did not match the enrollment. " +
                "Please ensure good lighting, face the camera directly, and make sure your ear is not covered by hair or accessories."
              : "Biometric verification failed. Your biometrics did not match the enrollment. Please try again.",
          );
          return;
        }

        setState("submitting");
        const challenge = await biometricApi.createChallenge({ voter_id: voterId });
        const signature = await signChallenge(privateKey, challenge.challenge);

        const verifyResult = await biometricApi.verifyBiometric({
          challenge_id: challenge.id,
          ...(enrolledDeviceId ? { device_id: enrolledDeviceId } : {}),
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
    [encryptedBundle, voterId, enrolledDeviceId, enrolledFace, enrolledEar],
  );

  const handleCaptureError = useCallback((message: string) => {
    setError(message);
    setState("error");
  }, []);

  const messages: Record<VerifyState, string> = {
    ready: "Verify your identity using your face and ear biometrics. No biometric data leaves this device.",
    loading: "Fetching your enrollment data\u2026",
    capturing: "",
    decrypting: "Verifying your biometrics and unlocking your signing key\u2026",
    submitting: "Submitting cryptographic proof to the server\u2026",
    success: "Identity verified! You can return to the voting website on your computer.",
    error: "Verification encountered a problem.",
    no_enrollment: "No biometric enrollment found for your account.",
    decrypt_failed: "Biometric verification failed.",
  };

  return (
    <PwaInstallGate>
    <div style={{ maxWidth: "480px", margin: "0 auto", padding: "1.5rem 1rem" }}>
      <h1 style={{ fontSize: "1.3rem", fontWeight: 700, textAlign: "center", color: theme.colors.text.primary }}>
        Biometric Verification
      </h1>

      {state !== "capturing" && (
        <div style={{ ...getCardStyle(theme), marginTop: "1.25rem" }}>
          <p style={{ color: theme.colors.text.primary, lineHeight: 1.6, fontSize: "0.95rem" }}>
            {messages[state]}
          </p>

          {error && (
            <p style={{ color: theme.colors.status.error, marginTop: theme.spacing.sm }}>{error}</p>
          )}

          {state === "success" && (
            <div style={{ marginTop: theme.spacing.md, ...getSuccessAlertStyle(theme), textAlign: "center" }}>
              <strong style={{ color: theme.colors.text.primary }}>Identity verified</strong>
              <p style={{ margin: `${theme.spacing.xs} 0 0 0`, fontSize: "0.9rem", color: theme.colors.text.primary }}>
                Your face and ear confirmed your identity. No biometric data was sent to the server.
              </p>
            </div>
          )}
        </div>
      )}

      {state === "capturing" && (
        <BiometricCaptureFlow
          mode="verify"
          onComplete={handleCaptureComplete}
          onError={handleCaptureError}
        />
      )}

      <div style={{ marginTop: "1.5rem", display: "flex", justifyContent: "center", gap: theme.spacing.md }}>
        {state === "ready" && (
          <PrimaryButton onClick={handleStartVerify}>Verify Identity</PrimaryButton>
        )}

        {(state === "loading" || state === "decrypting" || state === "submitting") && (
          <PrimaryButton disabled>Verifying\u2026</PrimaryButton>
        )}

        {(state === "error" || state === "no_enrollment" || state === "decrypt_failed") && (
          <>
            <SecondaryButton onClick={() => navigate("/auth")}>Back to Scanner</SecondaryButton>
            <PrimaryButton onClick={handleStartVerify}>Retry</PrimaryButton>
          </>
        )}

        {state === "success" && (
          <PrimaryButton onClick={() => navigate("/auth")}>Back to Scanner</PrimaryButton>
        )}
      </div>
    </div>
    </PwaInstallGate>
  );
}

export default AuthVerifyPage;
