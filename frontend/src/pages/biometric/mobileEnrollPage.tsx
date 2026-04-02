/**
 * Mobile Biometric Enrollment Page
 *
 * Accessed by scanning the QR code shown on the desktop registration flow.
 * Captures face + ear biometrics on the voter's mobile device, generates
 * an ECDSA P-256 keypair encrypted with a biometric-derived AES key, and
 * registers only the public key with the server.
 *
 * Flow:
 *   1. Capture face via front camera  -> extract 128-d descriptor
 *   2. Capture ear via rear camera    -> extract 128-d descriptor
 *   3. Generate ECDSA keypair, encrypt private key with biometric-derived key
 *   4. Store encrypted key + templates locally in IndexedDB
 *   5. Send public key to server
 */

import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { useTheme } from "../../styles/ThemeContext";
import { getCardStyle, getPageTitleStyle, PrimaryButton } from "../../styles/ui";
import { BiometricApiRepository } from "../../features/voter/repositories/biometric-api.repository";
import BiometricCaptureFlow from "../../features/biometric/components/BiometricCaptureFlow";
import { generateAndEncryptKeyPair } from "../../features/biometric/services/biometric-key-encryption.service";
import { storeBiometricData } from "../../features/biometric/services/biometric-storage.service";
import { FeatureDescriptor } from "../../features/biometric/models/biometric-feature.model";

const biometricApi = new BiometricApiRepository();

function getOrCreateDeviceId(): string {
  const STORAGE_KEY = "evoting_device_id";
  let deviceId = localStorage.getItem(STORAGE_KEY);
  if (!deviceId) {
    deviceId = crypto.randomUUID();
    localStorage.setItem(STORAGE_KEY, deviceId);
  }
  return deviceId;
}

type EnrollState =
  | "ready"
  | "capturing"
  | "generating_keys"
  | "enrolling"
  | "success"
  | "error";

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

  const handleStartEnroll = useCallback(() => {
    setState("capturing");
    setError(null);
  }, []);

  const handleCaptureComplete = useCallback(
    async (result: { faceDescriptor: FeatureDescriptor; earDescriptor: FeatureDescriptor }) => {
      if (!voterId) return;

      try {
        setState("generating_keys");

        // Generate ECDSA keypair and encrypt private key with biometric-derived key.
        const { publicKeyPem, encryptedBundle } = await generateAndEncryptKeyPair(
          result.faceDescriptor,
          result.earDescriptor,
        );

        // Persist biometric templates + encrypted key locally.
        await storeBiometricData({
          voterId,
          faceTemplate: Array.from(result.faceDescriptor),
          earTemplate: Array.from(result.earDescriptor),
          encryptedKeyBundle: encryptedBundle,
          enrolledAt: new Date().toISOString(),
        });

        setState("enrolling");

        // Register the public key with the server.
        const deviceId = getOrCreateDeviceId();
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
    },
    [voterId],
  );

  const handleCaptureError = useCallback((message: string) => {
    setError(message);
    setState("error");
  }, []);

  const messages: Record<EnrollState, string> = {
    ready:
      "This device will be linked to your voter account. " +
      "Your face and ear biometrics will be captured and stored only on this device \u2014 " +
      "the server will only receive a cryptographic public key.",
    capturing: "",
    generating_keys:
      "Generating biometric-bound encryption keys\u2026 " +
      "Your private signing key is being encrypted with your biometric features.",
    enrolling: "Registering your device with the voting platform\u2026",
    success:
      "Your device has been successfully enrolled! " +
      "Your face and ear biometrics are stored securely on this device only. " +
      "You can now close this page and return to the registration screen on your computer.",
    error: "Something went wrong during enrollment.",
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
        Biometric Enrollment
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
              <strong>Device enrolled</strong>
              <p style={{ margin: `${theme.spacing.xs} 0 0 0`, fontSize: "0.9rem" }}>
                Biometric modalities: face + ear (stored on device only)
              </p>
              <p style={{ margin: `${theme.spacing.xs} 0 0 0`, fontSize: "0.85rem", color: "#666" }}>
                Your signing key is encrypted with your biometric features and cannot be used without your face and ear.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Biometric capture flow */}
      {state === "capturing" && (
        <BiometricCaptureFlow
          mode="enroll"
          onComplete={handleCaptureComplete}
          onError={handleCaptureError}
        />
      )}

      {/* Action buttons */}
      <div style={{ marginTop: "1.5rem", display: "flex", justifyContent: "center" }}>
        {state === "ready" && (
          <PrimaryButton onClick={handleStartEnroll}>Start Enrollment</PrimaryButton>
        )}

        {(state === "generating_keys" || state === "enrolling") && (
          <PrimaryButton disabled>
            {state === "generating_keys" ? "Generating keys\u2026" : "Enrolling\u2026"}
          </PrimaryButton>
        )}

        {state === "error" && (
          <PrimaryButton onClick={handleStartEnroll}>Retry</PrimaryButton>
        )}
      </div>
    </div>
  );
}

export default MobileEnrollPage;
