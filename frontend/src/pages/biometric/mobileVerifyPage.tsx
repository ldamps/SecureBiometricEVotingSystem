/**
 * Mobile Biometric Verification Page
 *
 * Accessed by scanning the QR code shown on the desktop voting flow.
 *
 * Flow:
 *   1. Fetch credential + encrypted key bundle from server.
 *   2. Load enrolled templates from IndexedDB — REQUIRED. If missing,
 *      force re-enrollment rather than fall through.
 *   3. Capture fresh biometrics; run the cosine-similarity gate against
 *      the enrolled templates. Reject impostors here before touching the key.
 *   4. Decrypt the ECDSA private key with the biometric-derived AES key.
 *   5. Sign the server challenge and submit.
 *
 * Both gates are blocking: the cosine-similarity check runs first and
 * rejects impostors, then the fuzzy-extractor decryption confirms the
 * capture is close enough to the enrolled biometric to recover the key.
 * The fuzzy extractor alone is too permissive against impostors on a
 * shared device, so the template gate is no longer advisory.
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
import { decryptPrivateKey, appendAdaptiveHelper } from "../../features/biometric/services/biometric-key-encryption.service";
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
  | "no_templates"
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
        setError(
          "No active biometric enrollment was found for your account. Please " +
          "complete biometric enrollment from the registration page before " +
          "attempting to verify.",
        );
        return;
      }

      // 2. Use local device_id if available (for server-side lookup), but
      //    don't block verification when Safari has purged IndexedDB.
      const localDeviceId = await getDeviceId();
      setEnrolledDeviceId(localDeviceId || active.device_id);

      // 3. Load enrolled templates from local IndexedDB — REQUIRED. The
      //    fuzzy extractor alone cannot reliably reject impostors on a
      //    shared device, so verification must run the cosine-similarity
      //    gate against enrolled templates. If they're missing (e.g. Safari
      //    purged IndexedDB), force re-enrollment rather than fall through.
      const stored = await retrieveBiometricData(voterId);
      if (!stored?.faceTemplate || !stored?.earTemplate) {
        setState("no_templates");
        setError(
          "This device is not enrolled for your account. Biometric verification " +
          "can only be performed on a device where you have previously enrolled. " +
          "Please re-enroll from the registration page on this device, or use " +
          "the device where you originally enrolled.",
        );
        return;
      }
      setEnrolledFace(new Float32Array(stored.faceTemplate));
      setEnrolledEar(new Float32Array(stored.earTemplate));

      setEncryptedBundle(JSON.parse(active.encrypted_key_bundle));
      setState("capturing");
    } catch (err: any) {
      setError(
        err?.message ||
          "Could not load your enrollment data from the server. Please check " +
          "your connection and try again.",
      );
      setState("error");
    }
  }, [voterId]);

  // After biometric capture completes — match, decrypt, sign, adapt.
  const handleCaptureComplete = useCallback(
    async (result: { faceDescriptors: FeatureDescriptor[]; earDescriptor: FeatureDescriptor }) => {
      if (!encryptedBundle || !voterId) return;

      const freshFace = result.faceDescriptors[0];

      try {
        setState("decrypting");

        // Blocking cosine-similarity gate — rejects impostors before the
        // key is ever touched. `handleStartVerify` guarantees templates
        // are loaded by the time we reach "capturing".
        if (!enrolledFace || !enrolledEar) {
          setState("no_templates");
          setError(
            "This device is not enrolled for your account. Biometric verification " +
            "can only be performed on a device where you have previously enrolled. " +
            "Please re-enroll from the registration page on this device, or use " +
            "the device where you originally enrolled.",
          );
          return;
        }
        const match = matchBoth(
          freshFace, enrolledFace,
          result.earDescriptor, enrolledEar,
        );
        if (!match.overallPassed) {
          setState("decrypt_failed");
          const failedModality =
            !match.face.passed && !match.ear.passed
              ? "face and ear did"
              : !match.face.passed
                ? "face did"
                : "ear did";
          setError(
            `Identity mismatch. Your ${failedModality} not match the enrolled ` +
            "biometric on this device. If this is your phone, ensure good " +
            "lighting, face the camera directly, and keep your ear unobstructed. " +
            "If verification keeps failing, re-enroll from the registration page.",
          );
          return;
        }

        // Second gate: dual-modality biometric-bound key decryption.
        // Both face AND ear must RS-decode to recover the AES key.
        let privateKey: CryptoKey;
        let recoveredFaceMessage: Uint8Array;
        let recoveredEarMessage: Uint8Array;
        try {
          ({ privateKey, recoveredFaceMessage, recoveredEarMessage } =
            await decryptPrivateKey(
              freshFace,
              result.earDescriptor,
              encryptedBundle,
            ));
        } catch (err: any) {
          setState("decrypt_failed");
          const isLegacyEnrollment =
            encryptedBundle.format !== "fuzzy-extractor-rs-v4";
          setError(
            isLegacyEnrollment
              ? "Your enrollment was created with an older format that no longer " +
                "supports the dual-modality (face + ear) cryptographic binding. " +
                "Please re-enroll once from the registration page."
              : err?.message ||
                "Could not unlock your signing key. Retry in similar lighting and " +
                "pose to your enrollment, with the ear unobstructed.",
          );
          return;
        }

        // Both modalities decoded successfully — fold the capture into
        // both helper sets to track lighting / angle drift over time.
        const rotatedBundle = appendAdaptiveHelper(
          encryptedBundle,
          recoveredFaceMessage,
          recoveredEarMessage,
          freshFace,
          result.earDescriptor,
        );

        setState("submitting");
        const challenge = await biometricApi.createChallenge({ voter_id: voterId });
        const signature = await signChallenge(privateKey, challenge.challenge);

        const verifyResult = await biometricApi.verifyBiometric({
          challenge_id: challenge.id,
          ...(enrolledDeviceId ? { device_id: enrolledDeviceId } : {}),
          signature,
          encrypted_key_bundle: JSON.stringify(rotatedBundle),
        });

        if (verifyResult.verified) {
          setState("success");
        } else {
          setError(
            verifyResult.message ||
              "The server rejected the verification signature. This can happen if " +
              "your enrollment on this device is out of sync with the server. " +
              "Please re-enroll from the registration page and try again.",
          );
          setState("error");
        }
      } catch (err: any) {
        setError(
          err?.message ||
            "Verification could not be completed due to a network or server error. " +
            "Please check your connection and try again.",
        );
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
    error: "Verification could not be completed.",
    no_enrollment: "No biometric enrollment is active for your account.",
    no_templates: "This device is not enrolled for your account.",
    decrypt_failed: "Biometric verification failed — identity not confirmed.",
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

        {(state === "error" ||
          state === "no_enrollment" ||
          state === "no_templates" ||
          state === "decrypt_failed") && (
          <PrimaryButton onClick={handleStartVerify}>Retry</PrimaryButton>
        )}


      </div>
    </div>
  );
}

export default MobileVerifyPage;
