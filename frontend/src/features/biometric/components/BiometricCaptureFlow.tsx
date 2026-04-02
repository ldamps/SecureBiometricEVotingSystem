/**
 * Multi-step biometric capture orchestrator.
 *
 * Steps through:
 *   1. Loading ML models
 *   2. Face capture + feature extraction
 *   3. Ear capture + feature extraction
 *   4. Callback with both descriptors
 *
 * Used by both enrollment and verification pages.
 */

import { useState, useCallback, useEffect } from "react";
import { useTheme } from "../../../styles/ThemeContext";
import { getCardStyle } from "../../../styles/ui";
import { useCameraStream } from "../hooks/useCameraStream";
import CameraCapture from "./CameraCapture";
import { loadFaceModels, extractFaceDescriptor, extractStableFaceDescriptor } from "../services/face-recognition.service";
import { loadEarModel, extractEarDescriptor, extractStableEarDescriptor } from "../services/ear-recognition.service";
import { FeatureDescriptor } from "../models/biometric-feature.model";

type CaptureStep = "loading" | "face" | "face_processing" | "ear" | "ear_processing" | "done" | "error";

interface BiometricCaptureFlowProps {
  /** "enroll" captures multiple samples and averages; "verify" captures one. */
  mode: "enroll" | "verify";
  onComplete: (result: { faceDescriptor: FeatureDescriptor; earDescriptor: FeatureDescriptor }) => void;
  onError: (message: string) => void;
}

function BiometricCaptureFlow({ mode, onComplete, onError }: BiometricCaptureFlowProps) {
  const { theme } = useTheme();
  const [step, setStep] = useState<CaptureStep>("loading");
  const [faceDescriptor, setFaceDescriptor] = useState<FeatureDescriptor | null>(null);
  const [statusText, setStatusText] = useState("Loading biometric models...");

  const faceCamera = useCameraStream("user");
  const earCamera = useCameraStream("environment");

  // Step 1: Load models.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setStatusText("Loading face recognition model...");
        await loadFaceModels();
        if (cancelled) return;
        setStatusText("Loading ear recognition model...");
        await loadEarModel();
        if (cancelled) return;
        setStep("face");
      } catch (err: any) {
        if (!cancelled) {
          onError(err.message || "Failed to load biometric models.");
          setStep("error");
        }
      }
    })();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Start the appropriate camera when the step changes.
  useEffect(() => {
    if (step === "face") {
      faceCamera.start();
      setStatusText("Position your face within the oval and press the capture button.");
    }
    if (step === "ear") {
      earCamera.start();
      setStatusText("Position your ear within the guide using the rear camera and press capture.");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  // Face capture handler.
  const handleFaceCapture = useCallback(async () => {
    if (!faceCamera.videoRef.current) return;
    setStep("face_processing");
    setStatusText("Extracting facial features...");

    try {
      const result =
        mode === "enroll"
          ? await extractStableFaceDescriptor(faceCamera.videoRef.current, 5, 300)
          : await extractFaceDescriptor(faceCamera.videoRef.current);

      if (!result) {
        setStatusText("No face detected. Please try again.");
        setStep("face");
        return;
      }

      setFaceDescriptor(result.descriptor);
      faceCamera.stop();
      setStep("ear");
    } catch (err: any) {
      onError(err.message || "Face extraction failed.");
      setStep("error");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, faceCamera]);

  // Ear capture handler.
  const handleEarCapture = useCallback(async () => {
    if (!earCamera.videoRef.current || !faceDescriptor) return;
    setStep("ear_processing");
    setStatusText("Extracting ear features...");

    try {
      const result =
        mode === "enroll"
          ? await extractStableEarDescriptor(earCamera.videoRef.current, 5, 300)
          : await extractEarDescriptor(earCamera.videoRef.current);

      if (!result) {
        setStatusText("Ear capture failed. Please try again.");
        setStep("ear");
        return;
      }

      earCamera.stop();
      setStep("done");
      onComplete({ faceDescriptor, earDescriptor: result.descriptor });
    } catch (err: any) {
      onError(err.message || "Ear extraction failed.");
      setStep("error");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, earCamera, faceDescriptor, onComplete, onError]);

  return (
    <div style={{ ...getCardStyle(theme), marginTop: "1rem" }}>
      {/* Status bar */}
      <p style={{ color: theme.colors.text.primary, fontSize: "0.95rem", marginBottom: theme.spacing.md }}>
        {statusText}
      </p>

      {/* Step indicator */}
      <div style={{ display: "flex", gap: theme.spacing.sm, marginBottom: theme.spacing.md }}>
        {(["face", "ear"] as const).map((s, i) => (
          <div
            key={s}
            style={{
              flex: 1,
              height: 4,
              borderRadius: 2,
              background:
                (step === s || step === `${s}_processing`)
                  ? (theme.colors.primary || "#2563eb")
                  : (i === 0 && (step === "ear" || step === "ear_processing" || step === "done"))
                    ? (theme.colors.status?.success || "#22c55e")
                    : (step === "done" && i === 1)
                      ? (theme.colors.status?.success || "#22c55e")
                      : "#e5e7eb",
            }}
          />
        ))}
      </div>

      {/* Loading spinner */}
      {step === "loading" && (
        <div style={{ textAlign: "center", padding: theme.spacing.lg }}>
          <div style={{ fontSize: "1.5rem" }}>Loading models...</div>
        </div>
      )}

      {/* Face capture */}
      {(step === "face" || step === "face_processing") && (
        <CameraCapture
          videoRef={faceCamera.videoRef}
          onCapture={handleFaceCapture}
          overlayShape="oval"
          instruction="Position your face within the oval"
          capturing={step === "face_processing"}
        />
      )}

      {/* Ear capture */}
      {(step === "ear" || step === "ear_processing") && (
        <CameraCapture
          videoRef={earCamera.videoRef}
          onCapture={handleEarCapture}
          overlayShape="ear"
          instruction="Hold your phone near your ear using the rear camera"
          capturing={step === "ear_processing"}
        />
      )}

      {/* Camera errors */}
      {(faceCamera.error || earCamera.error) && (
        <p style={{ color: theme.colors.status?.error || "#ef4444", marginTop: theme.spacing.sm }}>
          {faceCamera.error || earCamera.error}
        </p>
      )}
    </div>
  );
}

export default BiometricCaptureFlow;
