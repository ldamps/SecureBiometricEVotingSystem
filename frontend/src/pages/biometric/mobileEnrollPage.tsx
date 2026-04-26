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
import { storeBiometricData, getOrCreateDeviceId } from "../../features/biometric/services/biometric-storage.service";
import { FeatureDescriptor } from "../../features/biometric/models/biometric-feature.model";

const biometricApi = new BiometricApiRepository();

const PWA_REDIRECT_KEY = "evoting_pwa_redirect";

/** True when the page is running as an installed PWA (Add to Home Screen). */
function isInstalledPwa(): boolean {
  if (typeof window === "undefined") return false;
  if ((navigator as any).standalone === true) return true;
  if (window.matchMedia("(display-mode: standalone)").matches) return true;
  return false;
}

/** Save the current URL so the PWA can resume here after install. */
function saveRedirectUrl(): void {
  localStorage.setItem(PWA_REDIRECT_KEY, window.location.href);
}

/** Detect iOS Safari so we can show platform-specific install instructions. */
function isIosSafari(): boolean {
  if (typeof navigator === "undefined") return false;
  const ua = navigator.userAgent;
  return /iP(hone|od|ad)/.test(ua) && /Safari/i.test(ua) && !/CriOS|FxiOS|OPiOS|EdgiOS/i.test(ua);
}

type EnrollState =
  | "install_pwa"
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

  const [state, setState] = useState<EnrollState>(() => {
    if (isInstalledPwa()) return "ready";
    // Save the full URL so the PWA can resume here after install.
    saveRedirectUrl();
    return "install_pwa";
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!voterId) {
      setError("Missing voter ID. Please scan the QR code again from the registration page.");
      setState("error");
    }
  }, [voterId]);

  const handleSkipInstall = useCallback(() => {
    setState("ready");
  }, []);

  const handleStartEnroll = useCallback(() => {
    setState("capturing");
    setError(null);
  }, []);

  const handleCaptureComplete = useCallback(
    async (result: { faceDescriptors: FeatureDescriptor[]; earDescriptor: FeatureDescriptor }) => {
      if (!voterId) return;

      try {
        setState("generating_keys");

        const { publicKeyPem, encryptedBundle } = await generateAndEncryptKeyPair(
          result.faceDescriptors,
          result.earDescriptor,
        );

        // Store every enrolment face descriptor. Verification compares
        // the fresh capture against all of them and uses the best
        // cosine — much more reliable than averaging or picking one.
        await storeBiometricData({
          voterId,
          faceTemplates: result.faceDescriptors.map((d) => Array.from(d)),
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
    install_pwa: "",
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

      {/* PWA install prompt */}
      {state === "install_pwa" && (
        <div style={{ ...getCardStyle(theme), marginTop: "1.25rem" }}>
          <p style={{ color: theme.colors.text.primary, lineHeight: 1.6, fontSize: "0.95rem", fontWeight: 600 }}>
            Install the Voting App first
          </p>
          <p style={{ color: theme.colors.text.primary, lineHeight: 1.6, fontSize: "0.95rem", marginTop: theme.spacing.sm }}>
            To keep your biometric data safe and persistent, please add this app to your home screen before enrolling.
          </p>

          {isIosSafari() ? (
            <ol style={{
              color: theme.colors.text.primary,
              lineHeight: 1.8,
              fontSize: "0.9rem",
              marginTop: theme.spacing.md,
              paddingLeft: "1.25rem",
            }}>
              <li>Tap the <strong>Share</strong> button at the bottom of Safari (the square with an arrow pointing up).</li>
              <li>Scroll down and tap <strong>&quot;Add to Home Screen&quot;</strong>.</li>
              <li>Tap <strong>&quot;Add&quot;</strong> in the top-right corner.</li>
              <li>Open the <strong>&quot;E-Voting&quot;</strong> app from your home screen.</li>
              <li>Scan the QR code again from within the app.</li>
            </ol>
          ) : (
            <ol style={{
              color: theme.colors.text.primary,
              lineHeight: 1.8,
              fontSize: "0.9rem",
              marginTop: theme.spacing.md,
              paddingLeft: "1.25rem",
            }}>
              <li>Tap the <strong>menu</strong> (three dots) in your browser.</li>
              <li>Tap <strong>&quot;Add to Home screen&quot;</strong> or <strong>&quot;Install app&quot;</strong>.</li>
              <li>Open the app from your home screen.</li>
              <li>Scan the QR code again from within the app.</li>
            </ol>
          )}

          <p style={{
            color: theme.colors.text.secondary,
            fontSize: "0.85rem",
            marginTop: theme.spacing.md,
            lineHeight: 1.5,
          }}>
            Installing the app ensures your biometric data is stored permanently on this device and won't be cleared by your browser.
          </p>

          <div style={{ marginTop: theme.spacing.lg, display: "flex", justifyContent: "center", gap: theme.spacing.md }}>
            <PrimaryButton onClick={handleSkipInstall}>
              Continue without installing
            </PrimaryButton>
          </div>
        </div>
      )}

      {/* Status / instructions */}
      {state !== "capturing" && state !== "install_pwa" && (
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
                backgroundColor: theme.colors.surfaceAlt,
                border: `1px solid ${theme.colors.status.success}`,
                textAlign: "center",
                color: theme.colors.text.primary,
              }}
            >
              <strong>Device enrolled</strong>
              <p style={{ margin: `${theme.spacing.xs} 0 0 0`, fontSize: "0.9rem" }}>
                Biometric modalities: face + ear (stored on device only)
              </p>
              <p style={{ margin: `${theme.spacing.xs} 0 0 0`, fontSize: "0.85rem", color: theme.colors.text.secondary }}>
                Your signing key is encrypted with your biometric features and cannot be used without your face and ear.
              </p>
              <p style={{ margin: `${theme.spacing.sm} 0 0 0`, fontSize: "0.85rem", color: theme.colors.text.secondary }}>
                You can now close this tab and return to the registration page.
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
