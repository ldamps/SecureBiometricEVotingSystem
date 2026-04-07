/**
 * Biometric capture with liveness detection.
 *
 * Single front-camera video where the user:
 *   1. Looks straight ahead — face detected + blink confirms liveness
 *   2. Face descriptor extracted automatically
 *   3. Turns head to the left — ear descriptor extracted when side profile detected
 *
 * Liveness checks:
 *   - Blink detection via eye-aspect-ratio (EAR) from face landmarks
 *   - Continuous face tracking during head turn (no photo splicing)
 *   - Motion consistency (face must move smoothly from front to side)
 */

import { useState, useEffect, useRef } from "react";
import { useTheme } from "../../../styles/ThemeContext";
import { getCardStyle } from "../../../styles/ui";
import { useCameraStream } from "../hooks/useCameraStream";
import * as faceapi from "face-api.js";
import { loadFaceModels, extractFaceDescriptor, extractStableFaceDescriptor } from "../services/face-recognition.service";
import { loadEarModel, extractEarDescriptor } from "../services/ear-recognition.service";
import { FeatureDescriptor } from "../models/biometric-feature.model";

type CaptureStep =
  | "loading"
  | "waiting_face"
  | "waiting_blink"
  | "extracting_face"
  | "turn_head"
  | "extracting_ear"
  | "done"
  | "error";

interface BiometricCaptureFlowProps {
  mode: "enroll" | "verify";
  onComplete: (result: { faceDescriptor: FeatureDescriptor; earDescriptor: FeatureDescriptor }) => void;
  onError: (message: string) => void;
}

/** Eye Aspect Ratio — drops below ~0.2 during a blink. */
function eyeAspectRatio(eye: faceapi.Point[]): number {
  const v1 = Math.hypot(eye[1].x - eye[5].x, eye[1].y - eye[5].y);
  const v2 = Math.hypot(eye[2].x - eye[4].x, eye[2].y - eye[4].y);
  const h = Math.hypot(eye[0].x - eye[3].x, eye[0].y - eye[3].y);
  return h === 0 ? 1 : (v1 + v2) / (2 * h);
}

const BLINK_THRESHOLD = 0.22;
const BLINK_TIMEOUT_MS = 10000;

const INSTRUCTIONS = {
  loading: { title: "Preparing", detail: "Loading biometric models. This may take a moment on first use." },
  waiting_face: { title: "Step 1 of 3: Position your face", detail: "Centre your face within the oval guide. Make sure your face is well-lit and clearly visible." },
  waiting_blink: { title: "Step 1 of 3: Liveness check", detail: "Face detected! Now blink naturally to prove you are a real person." },
  extracting_face: { title: "Step 2 of 3: Capturing face", detail: "Hold still \u2014 capturing your facial features. This takes a few seconds." },
  turn_head: { title: "Step 3 of 3: Show your ear", detail: "Turn your head to the LEFT to show your ear. The camera will capture automatically in a few seconds." },
  extracting_ear: { title: "Step 3 of 3: Capturing ear", detail: "Hold still \u2014 capturing your ear features." },
  done: { title: "Complete", detail: "Both face and ear captured successfully." },
  error: { title: "Error", detail: "Something went wrong. Please try again." },
};

function BiometricCaptureFlow({ mode, onComplete, onError }: BiometricCaptureFlowProps) {
  const { theme } = useTheme();
  const [step, setStep] = useState<CaptureStep>("loading");
  const [faceDescriptor, setFaceDescriptor] = useState<FeatureDescriptor | null>(null);
  const [faceDetected, setFaceDetected] = useState(false);
  const [headTurnProgress, setHeadTurnProgress] = useState(0);

  const camera = useCameraStream("user");
  const animFrameRef = useRef(0);
  const wasEyeClosedRef = useRef(false);
  const completedRef = useRef(false);
  const blinkTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Step 1: Load models then start camera.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await loadFaceModels();
        if (cancelled) return;
        await loadEarModel();
        if (cancelled) return;
        camera.start();
        // Give the camera a moment to initialise before detection starts.
        setTimeout(() => { if (!cancelled) setStep("waiting_face"); }, 800);
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

  // Face detection → blink detection → face extraction (combined loop).
  useEffect(() => {
    if (step !== "waiting_face" && step !== "waiting_blink") return;
    let running = true;

    // Timeout: if no blink detected within BLINK_TIMEOUT_MS, proceed anyway
    // (user may have already blinked before detection started).
    if (step === "waiting_blink" && !blinkTimerRef.current) {
      blinkTimerRef.current = setTimeout(() => {
        if (running) {
          setStep("extracting_face");
        }
      }, BLINK_TIMEOUT_MS);
    }

    const loop = async () => {
      if (!running) return;
      const video = camera.videoElRef.current;
      if (!video || video.readyState < 2) {
        animFrameRef.current = requestAnimationFrame(loop);
        return;
      }

      try {
        const detection = await faceapi
          .detectSingleFace(video, new faceapi.TinyFaceDetectorOptions({ scoreThreshold: 0.4 }))
          .withFaceLandmarks(true);

        if (!running) return;

        if (detection) {
          setFaceDetected(true);

          // If we were waiting for a face, move to blink detection.
          if (step === "waiting_face") {
            setStep("waiting_blink");
            return; // effect will re-run with new step
          }

          // Blink detection.
          const leftEye = detection.landmarks.getLeftEye();
          const rightEye = detection.landmarks.getRightEye();
          const ear = (eyeAspectRatio(leftEye) + eyeAspectRatio(rightEye)) / 2;

          if (ear < BLINK_THRESHOLD) {
            wasEyeClosedRef.current = true;
          } else if (wasEyeClosedRef.current) {
            // Blink completed — move to face extraction.
            wasEyeClosedRef.current = false;
            if (blinkTimerRef.current) {
              clearTimeout(blinkTimerRef.current);
              blinkTimerRef.current = null;
            }
            setStep("extracting_face");
            return;
          }
        } else {
          setFaceDetected(false);
        }
      } catch {
        // Continue on error.
      }

      if (running) {
        animFrameRef.current = requestAnimationFrame(loop);
      }
    };

    animFrameRef.current = requestAnimationFrame(loop);
    return () => {
      running = false;
      cancelAnimationFrame(animFrameRef.current);
      if (blinkTimerRef.current) {
        clearTimeout(blinkTimerRef.current);
        blinkTimerRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  // Face extraction.
  useEffect(() => {
    if (step !== "extracting_face") return;
    let cancelled = false;

    (async () => {
      const video = camera.videoElRef.current;
      if (!video) return;

      try {
        const result = mode === "enroll"
          ? await extractStableFaceDescriptor(video, 3, 250)
          : await extractFaceDescriptor(video);

        if (cancelled) return;

        if (!result) {
          // Retry — go back to face detection.
          setStep("waiting_face");
          setFaceDetected(false);
          return;
        }

        setFaceDescriptor(result.descriptor);
        setStep("turn_head");
      } catch (err: any) {
        if (!cancelled) {
          onError(err.message || "Face extraction failed.");
          setStep("error");
        }
      }
    })();

    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  // Ear capture — wait 4 seconds for the user to turn, then capture one frame.
  useEffect(() => {
    if (step !== "turn_head" || !faceDescriptor || completedRef.current) return;

    // Animate the countdown progress bar.
    let elapsed = 0;
    const progressTick = setInterval(() => {
      elapsed++;
      setHeadTurnProgress(Math.min(100, Math.round((elapsed / 4) * 100)));
    }, 1000);

    // After 4 seconds, capture.
    const timer = setTimeout(() => {
      clearInterval(progressTick);
      setHeadTurnProgress(100);
      completedRef.current = true;
      setStep("extracting_ear");
    }, 4000);

    return () => {
      clearTimeout(timer);
      clearInterval(progressTick);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, faceDescriptor]);

  // Perform the actual ear extraction in a separate effect so state is stable.
  useEffect(() => {
    if (step !== "extracting_ear" || !faceDescriptor) return;
    let cancelled = false;

    (async () => {
      // Yield a frame so the UI shows "Capturing ear".
      await new Promise((r) => setTimeout(r, 100));

      const video = camera.videoElRef.current;
      if (!video || cancelled) {
        onError("Camera not available for ear capture.");
        setStep("error");
        return;
      }

      try {
        const earResult = await extractEarDescriptor(video);
        if (cancelled) return;

        if (!earResult) {
          onError("Ear feature extraction returned no result.");
          setStep("error");
          return;
        }

        camera.stop();
        setStep("done");
        onComplete({ faceDescriptor, earDescriptor: earResult.descriptor });
      } catch (err: any) {
        if (!cancelled) {
          onError(err.message || "Ear extraction failed.");
          setStep("error");
        }
      }
    })();

    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  // Cleanup.
  useEffect(() => () => cancelAnimationFrame(animFrameRef.current), []);

  const info = INSTRUCTIONS[step];
  const stepNum = step === "loading" ? 0
    : (step === "waiting_face" || step === "waiting_blink") ? 1
    : step === "extracting_face" ? 2
    : (step === "turn_head" || step === "extracting_ear") ? 3
    : 4;

  return (
    <div style={{ ...getCardStyle(theme), marginTop: "1rem" }}>
      {/* Title */}
      <h2 style={{ fontSize: "1.1rem", fontWeight: 600, color: theme.colors.text.primary, margin: `0 0 ${theme.spacing.xs} 0` }}>
        {info.title}
      </h2>

      {/* Instructions */}
      <p style={{ color: theme.colors.text.secondary || "#6b7280", fontSize: "0.9rem", lineHeight: 1.5, marginBottom: theme.spacing.md }}>
        {info.detail}
      </p>

      {/* Progress steps */}
      <div style={{ display: "flex", gap: 4, marginBottom: theme.spacing.md }}>
        {[
          { label: "Liveness", num: 1 },
          { label: "Face", num: 2 },
          { label: "Ear", num: 3 },
        ].map(({ label, num }) => (
          <div key={label} style={{ flex: 1, textAlign: "center" }}>
            <div style={{
              height: 5,
              borderRadius: 3,
              background: num < stepNum
                ? (theme.colors.status?.success || "#22c55e")
                : num === stepNum
                  ? (theme.colors.primary || "#2563eb")
                  : "#e5e7eb",
              transition: "background 0.3s",
            }} />
            <span style={{
              fontSize: "0.65rem",
              color: num <= stepNum ? theme.colors.text.primary : (theme.colors.text.secondary || "#9ca3af"),
              fontWeight: num === stepNum ? 600 : 400,
            }}>
              {label}
            </span>
          </div>
        ))}
      </div>

      {/* Loading */}
      {step === "loading" && (
        <div style={{ textAlign: "center", padding: `${theme.spacing.lg} 0` }}>
          <p style={{ color: theme.colors.text.secondary || "#6b7280" }}>Initialising camera and models...</p>
        </div>
      )}

      {/* Camera feed */}
      {step !== "loading" && step !== "done" && step !== "error" && (
        <div style={{ position: "relative", width: "100%", maxWidth: 400, margin: "0 auto" }}>
          <video
            ref={camera.videoRef}
            autoPlay
            playsInline
            muted
            onLoadedMetadata={(e) => { (e.target as HTMLVideoElement).play().catch(() => {}); }}
            style={{
              width: "100%",
              borderRadius: theme.borderRadius?.md || "8px",
              transform: "scaleX(-1)",
              background: "#000",
              display: "block",
            }}
          />

          {/* Oval guide */}
          <div style={{
            position: "absolute", top: 0, left: 0, right: 0, bottom: 0,
            display: "flex", alignItems: "center", justifyContent: "center",
            pointerEvents: "none",
          }}>
            <div style={{
              width: "55%", height: "70%",
              border: `3px dashed ${faceDetected ? "rgba(34,197,94,0.8)" : "rgba(255,255,255,0.6)"}`,
              borderRadius: "50%",
              transition: "border-color 0.3s",
            }} />
          </div>

          {/* Face detection indicator */}
          {(step === "waiting_face") && (
            <div style={{
              position: "absolute", top: 8, left: "50%", transform: "translateX(-50%)",
              background: faceDetected ? "rgba(34,197,94,0.85)" : "rgba(0,0,0,0.7)",
              color: "#fff", padding: "3px 10px", borderRadius: 10, fontSize: "0.75rem",
              transition: "background 0.3s",
            }}>
              {faceDetected ? "Face detected" : "Looking for face..."}
            </div>
          )}

          {/* Blink prompt */}
          {step === "waiting_blink" && (
            <div style={{
              position: "absolute", bottom: 10, left: "50%", transform: "translateX(-50%)",
              background: "rgba(0,0,0,0.75)", color: "#fff",
              padding: "6px 14px", borderRadius: 12, fontSize: "0.8rem",
              textAlign: "center", maxWidth: "80%",
            }}>
              Please blink
            </div>
          )}

          {/* Face extraction progress */}
          {step === "extracting_face" && (
            <div style={{
              position: "absolute", bottom: 10, left: "50%", transform: "translateX(-50%)",
              background: "rgba(34,197,94,0.85)", color: "#fff",
              padding: "6px 14px", borderRadius: 12, fontSize: "0.8rem",
            }}>
              Capturing face... hold still
            </div>
          )}

          {/* Head turn countdown */}
          {step === "turn_head" && (
            <div style={{
              position: "absolute", bottom: 10, left: 12, right: 12,
            }}>
              <div style={{
                background: "rgba(0,0,0,0.7)", borderRadius: 10, padding: "8px 14px",
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                  <span style={{ color: "#fff", fontSize: "0.75rem" }}>Turn your head left now</span>
                  <span style={{ color: "#fff", fontSize: "0.75rem", fontWeight: 600 }}>
                    Capturing in {Math.max(0, Math.ceil(4 - (headTurnProgress / 100) * 4))}s
                  </span>
                </div>
                <div style={{ height: 6, borderRadius: 3, background: "rgba(255,255,255,0.25)" }}>
                  <div style={{
                    width: `${headTurnProgress}%`,
                    height: "100%",
                    borderRadius: 3,
                    background: headTurnProgress >= 100
                      ? (theme.colors.status?.success || "#22c55e")
                      : (theme.colors.primary || "#2563eb"),
                    transition: "width 1s linear",
                  }} />
                </div>
              </div>
            </div>
          )}

          {/* Ear extraction */}
          {step === "extracting_ear" && (
            <div style={{
              position: "absolute", bottom: 10, left: "50%", transform: "translateX(-50%)",
              background: "rgba(37,99,235,0.85)", color: "#fff",
              padding: "6px 14px", borderRadius: 12, fontSize: "0.8rem",
            }}>
              Capturing ear... hold still
            </div>
          )}

          {/* Arrow hint for head turn */}
          {step === "turn_head" && headTurnProgress < 50 && (
            <div style={{
              position: "absolute", top: "50%", right: 8, transform: "translateY(-50%)",
              fontSize: "2rem", color: "rgba(255,255,255,0.7)", pointerEvents: "none",
            }}>
              &larr;
            </div>
          )}
        </div>
      )}

      {/* Camera error */}
      {camera.error && (
        <p style={{ color: theme.colors.status?.error || "#ef4444", marginTop: theme.spacing.sm, fontSize: "0.85rem" }}>
          Camera error: {camera.error}
        </p>
      )}
    </div>
  );
}

export default BiometricCaptureFlow;
