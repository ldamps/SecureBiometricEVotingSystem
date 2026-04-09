/**
 * Authenticator PWA — Biometric Enrollment
 *
 * Identical logic to mobileEnrollPage.tsx but without the PWA install
 * gate. The user is already inside the installed authenticator app.
 * After success/error, a "Back to Scanner" button returns to /auth.
 */

import { useState, useEffect, useCallback } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useTheme } from "../../styles/ThemeContext";
import { getCardStyle, PrimaryButton, SecondaryButton } from "../../styles/ui";
import { BiometricApiRepository } from "../../features/voter/repositories/biometric-api.repository";
import BiometricCaptureFlow from "../../features/biometric/components/BiometricCaptureFlow";
import { generateAndEncryptKeyPair } from "../../features/biometric/services/biometric-key-encryption.service";
import { storeBiometricData, getOrCreateDeviceId } from "../../features/biometric/services/biometric-storage.service";
import { FeatureDescriptor } from "../../features/biometric/models/biometric-feature.model";
import PwaInstallGate from "../../features/biometric/components/PwaInstallGate";

const biometricApi = new BiometricApiRepository();

type EnrollState = "ready" | "capturing" | "generating_keys" | "enrolling" | "success" | "error";

function AuthEnrollPage() {
  const { theme } = useTheme();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const voterId = searchParams.get("voter_id");

  const [state, setState] = useState<EnrollState>("ready");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!voterId) {
      setError("Missing voter ID. Go back and scan the QR code again.");
      setState("error");
    }
  }, [voterId]);

  const handleStartEnroll = useCallback(() => {
    setState("capturing");
    setError(null);
  }, []);

  const handleCaptureComplete = useCallback(
    async (result: { faceDescriptor: FeatureDescriptor; earDescriptor: FeatureDescriptor }) => {
      if (!voterId) return;
      try {
        setState("generating_keys");

        const { publicKeyPem, encryptedBundle } = await generateAndEncryptKeyPair(
          result.faceDescriptor,
          result.earDescriptor,
        );

        await storeBiometricData({
          voterId,
          faceTemplate: Array.from(result.faceDescriptor),
          earTemplate: Array.from(result.earDescriptor),
          encryptedKeyBundle: encryptedBundle,
          enrolledAt: new Date().toISOString(),
        });

        setState("enrolling");

        const deviceId = await getOrCreateDeviceId();
        await biometricApi.enrollDevice({
          voter_id: voterId,
          public_key_pem: publicKeyPem,
          device_id: deviceId,
          modalities: "face+ear",
          device_label: navigator.userAgent.slice(0, 100),
          encrypted_key_bundle: JSON.stringify(encryptedBundle),
        });

        setState("success");
      } catch (err: any) {
        setError(err.message || "Enrollment failed. Please try again.");
        setState("error");
      }
    },
    [voterId],
  );

  const handleCaptureError = useCallback((message: string) => {
    setError(message);
    setState("error");
  }, []);

  const messages: Record<EnrollState, string> = {
    ready:
      "Your face and ear biometrics will be captured and stored only on this device. " +
      "The server will only receive a cryptographic public key.",
    capturing: "",
    generating_keys: "Generating biometric-bound encryption keys\u2026",
    enrolling: "Registering your device with the voting platform\u2026",
    success:
      "Enrollment complete! Your biometrics are stored securely on this device. " +
      "You can return to the voting website on your computer.",
    error: "Something went wrong during enrollment.",
  };

  return (
    <PwaInstallGate>
    <div style={{ maxWidth: "480px", margin: "0 auto", padding: "1.5rem 1rem" }}>
      <h1 style={{ fontSize: "1.3rem", fontWeight: 700, textAlign: "center", color: theme.colors.text.primary }}>
        Biometric Enrollment
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
            <div style={{
              marginTop: theme.spacing.md,
              padding: theme.spacing.md,
              borderRadius: theme.borderRadius?.md || "8px",
              backgroundColor: theme.colors.surfaceAlt,
              border: `1px solid ${theme.colors.status.success}`,
              textAlign: "center",
              color: theme.colors.text.primary,
            }}>
              <strong>Device enrolled</strong>
              <p style={{ margin: `${theme.spacing.xs} 0 0 0`, fontSize: "0.9rem" }}>
                Biometric modalities: face + ear (stored on device only)
              </p>
            </div>
          )}
        </div>
      )}

      {state === "capturing" && (
        <BiometricCaptureFlow
          mode="enroll"
          onComplete={handleCaptureComplete}
          onError={handleCaptureError}
        />
      )}

      <div style={{ marginTop: "1.5rem", display: "flex", justifyContent: "center", gap: theme.spacing.md }}>
        {state === "ready" && (
          <PrimaryButton onClick={handleStartEnroll}>Start Enrollment</PrimaryButton>
        )}

        {(state === "generating_keys" || state === "enrolling") && (
          <PrimaryButton disabled>
            {state === "generating_keys" ? "Generating keys\u2026" : "Enrolling\u2026"}
          </PrimaryButton>
        )}

        {state === "error" && (
          <>
            <SecondaryButton onClick={() => navigate("/auth")}>Back to Scanner</SecondaryButton>
            <PrimaryButton onClick={handleStartEnroll}>Retry</PrimaryButton>
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

export default AuthEnrollPage;
