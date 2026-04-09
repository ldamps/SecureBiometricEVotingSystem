/**
 * Mobile Biometric Verification Page
 *
 * Accessed by scanning the QR code shown on the desktop voting flow.
 *
 * Flow:
 *   1. Fetch credential + encrypted key bundle from server.
 *   2. Load enrolled templates from IndexedDB if available (optional gate).
 *   3. Capture fresh biometrics; run template matching gate when templates exist.
 *   4. Decrypt the ECDSA private key with the biometric-derived AES key.
 *   5. Sign the server challenge and submit.
 *
 * The biometric key decryption (step 4) is the primary security gate —
 * only the correct face + ear can recover the signing key.  The template
 * matching gate (step 3) provides better error messages when local
 * templates are available, but is skipped when Safari has purged IndexedDB.
 *
 * No biometric data ever leaves the device — only a cryptographic
 * signature is sent to the server.
 */

import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { useTheme } from "../../styles/ThemeContext";
import { getCardStyle, getPageTitleStyle, getSuccessAlertStyle, PrimaryButton } from "../../styles/ui";
import { BiometricApiRepository } from "../../features/voter/repositories/biometric-api.repository";
import BiometricCaptureFlow from "../../features/biometric/components/BiometricCaptureFlow";
import { decryptPrivateKey } from "../../features/biometric/services/biometric-key-encryption.service";
import { matchBoth } from "../../features/biometric/services/biometric-matching.service";
import { retrieveBiometricData, getDeviceId } from "../../features/biometric/services/biometric-storage.service";
import { FeatureDescriptor, EncryptedKeyBundle } from "../../features/biometric/models/biometric-feature.model";

const biometricApi = new BiometricApiRepository();
const PWA_REDIRECT_KEY = "evoting_pwa_redirect";

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
  return btoa(String.fromCharCode.apply(null, Array.from(new Uint8Array(signature))));
}

type VerifyState =
  | "ready"
  | "loading"
  | "capturing"
  | "decrypting"
  | "submitting"
  | "success"
  | "error"
  | "no_enrollment"
  | "decrypt_failed";

function MobileVerifyPage() {
  const { theme } = useTheme();
  const [searchParams] = useSearchParams();
  const challengeId = searchParams.get("challenge_id");
  const voterId = searchParams.get("voter_id");

  const [state, setState] = useState<VerifyState>("ready");
  const [error, setError] = useState<string | null>(null);
  const [encryptedBundle, setEncryptedBundle] = useState<EncryptedKeyBundle | null>(null);
  const [enrolledDeviceId, setEnrolledDeviceId] = useState<string>("");
  const [enrolledFace, setEnrolledFace] = useState<FeatureDescriptor | null>(null);
  const [enrolledEar, setEnrolledEar] = useState<FeatureDescriptor | null>(null);

  // Save URL so PWA can resume here after install.
  useEffect(() => {
    localStorage.setItem(PWA_REDIRECT_KEY, window.location.href);
  }, []);

  useEffect(() => {
    if (!challengeId || !voterId) {
      setError("Missing challenge or voter ID. Please scan the QR code again.");
      setState("error");
    }
  }, [challengeId, voterId]);

  // Fetch credential from server and load local templates if available.
  const handleStartVerify = useCallback(async () => {
    if (!voterId) return;
    setError(null);
    setState("loading");

    try {
      // 1. Fetch credential from server
      const credentials = await biometricApi.listCredentials(voterId);
      const active = credentials.find((c) => c.is_active && c.encrypted_key_bundle);

      if (!active || !active.encrypted_key_bundle) {
        setState("no_enrollment");
        setError("No biometric enrollment found. Please complete enrollment first.");
        return;
      }

      // 2. Use local device_id if available (for server-side lookup), but
      //    don't block verification when Safari has purged IndexedDB.
      const localDeviceId = await getDeviceId();
      setEnrolledDeviceId(localDeviceId || active.device_id);

      // 3. Load enrolled templates from local IndexedDB if available.
      //    When present, we run an extra template-matching gate for better
      //    error messages. When absent (Safari purged storage), we skip the
      //    gate and rely on biometric key decryption as the security check.
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

  // After biometric capture completes — match, decrypt, and sign.
  const handleCaptureComplete = useCallback(
    async (result: { faceDescriptor: FeatureDescriptor; earDescriptor: FeatureDescriptor }) => {
      if (!encryptedBundle || !voterId) return;

      try {
        setState("decrypting");

        // If enrolled templates are available locally, run an advisory
        // matching check.  A failure here does NOT block verification —
        // the real security gate is the biometric key decryption below.
        // We record the result so we can show a more helpful error
        // message if key decryption also fails.
        let templateMatchFailed = false;
        if (enrolledFace && enrolledEar) {
          const match = matchBoth(
            result.faceDescriptor, enrolledFace,
            result.earDescriptor, enrolledEar,
          );
          templateMatchFailed = !match.overallPassed;
        }

        // Attempt to decrypt the signing key with fresh biometrics.
        // This is the primary security gate — only the correct face +
        // ear can recover the ECDSA private key via AES-GCM decryption.
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
              : "Biometric verification failed. Your face and ear did not match " +
                "the enrollment closely enough to unlock the signing key. Please try again.",
          );
          return;
        }

        // Request a fresh challenge and sign it.
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
    ready:
      "Verify your identity using your face and ear biometrics. " +
      "Your biometric data never leaves this device \u2014 only a cryptographic " +
      "signature is sent to confirm your identity.",
    loading: "Fetching your enrollment data\u2026",
    capturing: "",
    decrypting: "Verifying your biometrics and unlocking your signing key\u2026",
    submitting: "Submitting cryptographic proof to the server\u2026",
    success:
      "Identity verified successfully! " +
      "You can now close this page and return to the voting screen. " +
      "It will update automatically.",
    error: "Verification encountered a problem.",
    no_enrollment: "No biometric enrollment found for your account.",
    decrypt_failed: "Biometric verification failed.",
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

          {state === "success" && (
            <div
              style={{
                marginTop: theme.spacing.md,
                ...getSuccessAlertStyle(theme),
                textAlign: "center",
              }}
            >
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

      <div style={{ marginTop: "1.5rem", display: "flex", justifyContent: "center" }}>
        {state === "ready" && (
          <PrimaryButton onClick={handleStartVerify}>Verify Identity</PrimaryButton>
        )}

        {(state === "loading" || state === "decrypting" || state === "submitting") && (
          <PrimaryButton disabled>Verifying\u2026</PrimaryButton>
        )}

        {(state === "error" || state === "no_enrollment" || state === "decrypt_failed") && (
          <PrimaryButton onClick={handleStartVerify}>Retry</PrimaryButton>
        )}


      </div>
    </div>
  );
}

export default MobileVerifyPage;
