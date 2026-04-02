/**
 * Reusable camera preview with a capture overlay and action button.
 */

import React from "react";
import { useTheme } from "../../../styles/ThemeContext";

interface CameraCaptureProps {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  onCapture: () => void;
  overlayShape: "oval" | "ear";
  instruction: string;
  capturing: boolean;
}

function CameraCapture({ videoRef, onCapture, overlayShape, instruction, capturing }: CameraCaptureProps) {
  const { theme } = useTheme();

  return (
    <div style={{ position: "relative", width: "100%", maxWidth: 400, margin: "0 auto" }}>
      {/* Video feed */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        style={{
          width: "100%",
          borderRadius: theme.borderRadius?.md || "8px",
          transform: overlayShape === "oval" ? "scaleX(-1)" : "none",
          background: "#000",
        }}
      />

      {/* Overlay guide */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            width: overlayShape === "oval" ? "55%" : "50%",
            height: overlayShape === "oval" ? "70%" : "60%",
            border: "3px dashed rgba(255,255,255,0.7)",
            borderRadius: overlayShape === "oval" ? "50%" : "40% 60% 60% 40%",
          }}
        />
      </div>

      {/* Instruction text */}
      <p
        style={{
          textAlign: "center",
          color: theme.colors.text.primary,
          marginTop: theme.spacing.sm,
          fontSize: "0.9rem",
        }}
      >
        {instruction}
      </p>

      {/* Capture button */}
      <div style={{ display: "flex", justifyContent: "center", marginTop: theme.spacing.sm }}>
        <button
          onClick={onCapture}
          disabled={capturing}
          style={{
            width: 64,
            height: 64,
            borderRadius: "50%",
            border: "4px solid #fff",
            background: capturing ? "#ccc" : theme.colors.primary || "#2563eb",
            cursor: capturing ? "not-allowed" : "pointer",
            transition: "background 0.2s",
          }}
          aria-label="Capture"
        />
      </div>
    </div>
  );
}

export default CameraCapture;
