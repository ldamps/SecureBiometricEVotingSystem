/**
 * Authenticator PWA home page.
 *
 * - If running as an installed PWA → shows the QR scanner.
 * - If opened in a regular browser tab → shows install instructions.
 */

import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useTheme } from "../../styles/ThemeContext";
import { getCardStyle, PrimaryButton } from "../../styles/ui";
import { parseQRCode } from "../../features/biometric/services/qr-parser.service";
import QRScannerView from "../../features/biometric/components/QRScannerView";

function isInstalledPwa(): boolean {
  if (typeof window === "undefined") return false;
  if ((navigator as any).standalone === true) return true;
  if (window.matchMedia("(display-mode: standalone)").matches) return true;
  return false;
}

function isIosSafari(): boolean {
  if (typeof navigator === "undefined") return false;
  const ua = navigator.userAgent;
  return /iP(hone|od|ad)/.test(ua) && /Safari/i.test(ua) && !/CriOS|FxiOS|OPiOS|EdgiOS/i.test(ua);
}

function AuthHomePage() {
  const { theme } = useTheme();
  const navigate = useNavigate();
  const [installed] = useState(isInstalledPwa);
  const [error, setError] = useState<string | null>(null);

  const handleScan = useCallback(
    (data: string) => {
      const action = parseQRCode(data);
      if (action.type === "enroll") {
        navigate(`/auth/enroll?voter_id=${encodeURIComponent(action.voterId)}`);
      } else if (action.type === "verify") {
        navigate(
          `/auth/verify?voter_id=${encodeURIComponent(action.voterId)}&challenge_id=${encodeURIComponent(action.challengeId)}`,
        );
      } else {
        setError("This QR code is not from the e-voting platform. Please scan the code shown on the voting website.");
      }
    },
    [navigate],
  );

  const handleError = useCallback((msg: string) => setError(msg), []);

  // ── Not installed: show install instructions ──────────────────────
  if (!installed) {
    return (
      <div style={{ maxWidth: "480px", margin: "0 auto", padding: "1.5rem 1rem" }}>
        <div style={{ ...getCardStyle(theme), marginTop: "1.25rem" }}>
          <p style={{ color: theme.colors.text.primary, lineHeight: 1.6, fontSize: "0.95rem", fontWeight: 600 }}>
            Install the Authenticator
          </p>
          <p style={{ color: theme.colors.text.primary, lineHeight: 1.6, fontSize: "0.95rem", marginTop: theme.spacing.sm }}>
            Add this app to your home screen so your biometric data is stored permanently and securely on your device.
          </p>

          {isIosSafari() ? (
            <ol style={{
              color: theme.colors.text.primary,
              lineHeight: 1.8,
              fontSize: "0.9rem",
              marginTop: theme.spacing.md,
              paddingLeft: "1.25rem",
            }}>
              <li>Tap the <strong>Share</strong> button at the bottom of Safari.</li>
              <li>Scroll down and tap <strong>&quot;Add to Home Screen&quot;</strong>.</li>
              <li>Tap <strong>&quot;Add&quot;</strong>.</li>
              <li>Open <strong>&quot;E-Vote Auth&quot;</strong> from your home screen.</li>
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
            </ol>
          )}
        </div>
      </div>
    );
  }

  // ── Installed PWA: show QR scanner ────────────────────────────────
  return (
    <div style={{ maxWidth: "480px", margin: "0 auto", padding: "1rem", flex: 1, display: "flex", flexDirection: "column" }}>
      <p style={{
        color: theme.colors.text.secondary,
        fontSize: "0.9rem",
        textAlign: "center",
        marginBottom: "0.75rem",
      }}>
        Scan the QR code shown on the voting website
      </p>

      <QRScannerView onScan={handleScan} onError={handleError} />

      {error && (
        <div style={{ ...getCardStyle(theme), marginTop: "1rem" }}>
          <p style={{ color: theme.colors.status.error, fontSize: "0.9rem" }}>
            {error}
          </p>
          <div style={{ marginTop: theme.spacing.sm, display: "flex", justifyContent: "center" }}>
            <PrimaryButton onClick={() => setError(null)}>Try Again</PrimaryButton>
          </div>
        </div>
      )}
    </div>
  );
}

export default AuthHomePage;
