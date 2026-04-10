/**
 * Full-viewport QR scanner component.
 *
 * Renders a rear-camera video feed with a transparent overlay and a
 * scan-area cutout.  Calls `onScan` with the decoded string when a
 * QR code is detected.
 */

import { useEffect } from "react";
import { useTheme } from "../../../styles/ThemeContext";
import { useQRScanner } from "../hooks/useQRScanner";

interface QRScannerViewProps {
  onScan: (data: string) => void;
  onError: (message: string) => void;
}

function QRScannerView({ onScan, onError }: QRScannerViewProps) {
  const { theme } = useTheme();
  const scanner = useQRScanner(onScan);

  useEffect(() => {
    scanner.start();
    return () => scanner.stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (scanner.error) onError(scanner.error);
  }, [scanner.error, onError]);

  return (
    <div
      style={{
        position: "relative",
        width: "100%",
        aspectRatio: "3/4",
        maxHeight: "70vh",
        borderRadius: theme.borderRadius?.md || "8px",
        overflow: "hidden",
        backgroundColor: "#000",
      }}
    >
      {/* Camera feed */}
      <video
        ref={scanner.videoRef}
        autoPlay
        playsInline
        muted
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
        }}
      />

      {/* Overlay with cutout */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {/* Semi-transparent background */}
        <div style={{ flex: 1, width: "100%", backgroundColor: "rgba(0,0,0,0.45)" }} />

        <div style={{ display: "flex", width: "100%" }}>
          <div style={{ flex: 1, backgroundColor: "rgba(0,0,0,0.45)" }} />

          {/* Scan area */}
          <div
            style={{
              width: "220px",
              height: "220px",
              border: "3px solid rgba(255,255,255,0.8)",
              borderRadius: "16px",
              position: "relative",
            }}
          >
            {/* Corner markers */}
            {[
              { top: -3, left: -3, borderTop: "4px solid #fff", borderLeft: "4px solid #fff" },
              { top: -3, right: -3, borderTop: "4px solid #fff", borderRight: "4px solid #fff" },
              { bottom: -3, left: -3, borderBottom: "4px solid #fff", borderLeft: "4px solid #fff" },
              { bottom: -3, right: -3, borderBottom: "4px solid #fff", borderRight: "4px solid #fff" },
            ].map((style, i) => (
              <div
                key={i}
                style={{
                  position: "absolute",
                  width: "28px",
                  height: "28px",
                  borderRadius: i < 2 ? "8px 0 0 0" : "0 0 8px 0",
                  ...style,
                } as React.CSSProperties}
              />
            ))}
          </div>

          <div style={{ flex: 1, backgroundColor: "rgba(0,0,0,0.45)" }} />
        </div>

        <div style={{ flex: 1, width: "100%", backgroundColor: "rgba(0,0,0,0.45)" }} />
      </div>

      {/* Hint text */}
      <div
        style={{
          position: "absolute",
          bottom: "1.5rem",
          left: 0,
          right: 0,
          textAlign: "center",
          color: "#fff",
          fontSize: "0.9rem",
          textShadow: "0 1px 3px rgba(0,0,0,0.7)",
        }}
      >
        Point at the QR code on the voting website
      </div>
    </div>
  );
}

export default QRScannerView;
