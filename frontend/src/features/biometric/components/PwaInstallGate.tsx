/**
 * Gate that blocks biometric enrollment/verification unless the app
 * is running as an installed PWA.  When installed, renders children.
 * When not installed, shows mandatory install instructions with no
 * skip option.
 *
 * This ensures biometric data is stored in the PWA's permanent
 * IndexedDB — not Safari's 7-day-eviction storage.
 */

import { useTheme } from "../../../styles/ThemeContext";
import { getCardStyle } from "../../../styles/ui";

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

function PwaInstallGate({ children }: { children: React.ReactNode }) {
  const { theme } = useTheme();

  if (isInstalledPwa()) {
    return <>{children}</>;
  }

  return (
    <div style={{ maxWidth: "480px", margin: "0 auto", padding: "1.5rem 1rem" }}>
      <h1 style={{ fontSize: "1.3rem", fontWeight: 700, textAlign: "center", color: theme.colors.text.primary }}>
        Install Required
      </h1>

      <div style={{ ...getCardStyle(theme), marginTop: "1.25rem" }}>
        <p style={{ color: theme.colors.text.primary, lineHeight: 1.6, fontSize: "0.95rem", fontWeight: 600 }}>
          Install the E-Voting Authenticator
        </p>
        <p style={{ color: theme.colors.text.primary, lineHeight: 1.6, fontSize: "0.95rem", marginTop: theme.spacing.sm }}>
          Your biometric data must be stored securely on your device. To prevent data loss, the authenticator app must be installed to your home screen before continuing.
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
            <li>Tap <strong>&quot;Add&quot;</strong>.</li>
            <li>Open <strong>&quot;E-Vote Auth&quot;</strong> from your home screen.</li>
            <li>Use the built-in QR scanner to scan the code on the voting website.</li>
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
            <li>Open <strong>&quot;E-Vote Auth&quot;</strong> from your home screen.</li>
            <li>Use the built-in QR scanner to scan the code on the voting website.</li>
          </ol>
        )}

        <p style={{
          color: theme.colors.status.error,
          fontSize: "0.85rem",
          marginTop: theme.spacing.md,
          lineHeight: 1.5,
          fontWeight: 600,
        }}>
          Biometric enrollment is only available from the installed app. This protects your data from being cleared when you clear your browser history.
        </p>
      </div>
    </div>
  );
}

export default PwaInstallGate;
