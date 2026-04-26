/**
 * Authenticator PWA — Biometric Verification
 *
 * Mirrors mobileVerifyPage.tsx (without PWA redirect bookkeeping). Both
 * pages MUST keep their verification logic in sync — in particular, the
 * blocking cosine-similarity gate and the no-templates refusal.
 */

import { useState, useEffect, useCallback } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useTheme } from "../../styles/ThemeContext";
import { getCardStyle, getSuccessAlertStyle, PrimaryButton, SecondaryButton } from "../../styles/ui";
import { BiometricApiRepository } from "../../features/voter/repositories/biometric-api.repository";
import BiometricCaptureFlow from "../../features/biometric/components/BiometricCaptureFlow";
import { decryptPrivateKey, appendAdaptiveHelper } from "../../features/biometric/services/biometric-key-encryption.service";
import { matchBoth } from "../../features/biometric/services/biometric-matching.service";
import { retrieveBiometricData, getDeviceId } from "../../features/biometric/services/biometric-storage.service";
import { FeatureDescriptor, EncryptedKeyBundle } from "../../features/biometric/models/biometric-feature.model";
// PwaInstallGate is intentionally NOT used for verification — the encrypted
// key bundle is fetched from the server, so IndexedDB persistence is not
// required.  Blocking verification behind PWA install would prevent voters
// who scan the QR code in a regular browser from completing the flow.

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
  | "submitting" | "success" | "error" | "no_enrollment"
  | "no_templates" | "decrypt_failed";

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
  const [enrolledFaces, setEnrolledFaces] = useState<FeatureDescriptor[] | null>(null);
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
        setError(
          "No active biometric enrollment was found for your account. Please " +
          "complete biometric enrollment from the registration page before " +
          "attempting to verify.",
        );
        return;
      }

      const localDeviceId = await getDeviceId();
      setEnrolledDeviceId(localDeviceId || active.device_id);

      // Enrolled templates are REQUIRED for verification. The fuzzy
      // extractor alone cannot reliably reject impostors — the cosine
      // gate against the enrolled templates is what stops someone else
      // verifying on this device.
      const stored = await retrieveBiometricData(voterId);
      const faceTemplates: number[][] | undefined =
        stored?.faceTemplates && stored.faceTemplates.length > 0
          ? stored.faceTemplates
          : stored?.faceTemplate
            ? [stored.faceTemplate]
            : undefined;
      if (!faceTemplates || !stored?.earTemplate) {
        setState("no_templates");
        setError(
          "This device is not enrolled for your account. Biometric " +
          "verification can only be performed on a device where you have " +
          "previously enrolled. Please re-enroll from the registration page " +
          "on this device, or use the device where you originally enrolled.",
        );
        return;
      }
      setEnrolledFaces(faceTemplates.map((t) => new Float32Array(t)));
      setEnrolledEar(new Float32Array(stored.earTemplate));

      setEncryptedBundle(JSON.parse(active.encrypted_key_bundle));
      setState("capturing");
    } catch (err: any) {
      setError(
        err?.message ||
          "Could not load your enrollment data from the server. Please " +
          "check your connection and try again.",
      );
      setState("error");
    }
  }, [voterId]);

  const handleCaptureComplete = useCallback(
    async (result: { faceDescriptors: FeatureDescriptor[]; earDescriptor: FeatureDescriptor }) => {
      if (!encryptedBundle || !voterId) return;

      const freshFace = result.faceDescriptors[0];

      try {
        setState("decrypting");

        // Blocking cosine-similarity gate — rejects impostors before the
        // encrypted key is ever touched. `handleStartVerify` guarantees
        // templates are loaded by the time we reach "capturing".
        if (!enrolledFaces || enrolledFaces.length === 0 || !enrolledEar) {
          setState("no_templates");
          setError(
            "This device is not enrolled for your account. Biometric " +
            "verification can only be performed on a device where you have " +
            "previously enrolled. Please re-enroll from the registration page " +
            "on this device, or use the device where you originally enrolled.",
          );
          return;
        }
        const match = matchBoth(
          freshFace, enrolledFaces,
          result.earDescriptor, enrolledEar,
        );
        const faceScore = match.face.similarity.toFixed(3);
        const earScore = match.ear.similarity.toFixed(3);
        // eslint-disable-next-line no-console
        console.log(
          `[biometric] cosine match — face=${faceScore} best of ${enrolledFaces.length} enrolled (need ≥ 0.92, ${match.face.passed ? "PASS" : "FAIL"}), ` +
          `ear=${earScore} (need ≥ 0.70, ${match.ear.passed ? "PASS" : "FAIL"})`,
        );
        if (!match.overallPassed) {
          setState("decrypt_failed");
          setError(
            "Biometric match unsuccessful. Please try again, ensuring good " +
            "lighting and that your ear is unobstructed.",
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
                "Could not unlock your signing key from this capture. Retry in " +
                "similar lighting and pose to your enrollment, with the ear " +
                "unobstructed.",
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
              "The server rejected the verification signature. This can " +
              "happen if your enrollment on this device is out of sync with " +
              "the server. Please re-enroll from the registration page and " +
              "try again.",
          );
          setState("error");
        }
      } catch (err: any) {
        setError(
          err?.message ||
            "Verification could not be completed due to a network or server " +
            "error. Please check your connection and try again.",
        );
        setState("error");
      }
    },
    [encryptedBundle, voterId, enrolledDeviceId, enrolledFaces, enrolledEar],
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
    error: "Verification could not be completed.",
    no_enrollment: "No biometric enrollment is active for your account.",
    no_templates: "This device is not enrolled for your account.",
    decrypt_failed: "Biometric verification failed — identity not confirmed.",
  };

  return (
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

        {(state === "error" ||
          state === "no_enrollment" ||
          state === "no_templates" ||
          state === "decrypt_failed") && (
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
  );
}

export default AuthVerifyPage;
