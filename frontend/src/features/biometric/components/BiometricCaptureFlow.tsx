/**
 * Biometric capture with liveness detection.
 *
 * Verification: one face capture, then head turn for ear.
 * Enrollment: three face captures under slightly varied pose (neutral,
 * chin-down, chin-up) to widen the cross-session drift envelope, then head
 * turn for ear. Verification later succeeds if the fresh capture is close
 * to ANY of the enrolled descriptors — so small pose/lighting variation
 * days later no longer causes hard failure.
 *
 * Liveness checks:
 *   - Blink detection via eye-aspect-ratio (EAR) from face landmarks
 *   - Continuous face tracking during head turn (no photo splicing)
 */

import { useState, useEffect, useRef } from "react";
import { useTheme } from "../../../styles/ThemeContext";
import { getCardStyle } from "../../../styles/ui";
import { useCameraStream } from "../hooks/useCameraStream";
import * as faceapi from "face-api.js";
import { loadFaceModels, extractStableFaceDescriptor } from "../services/face-recognition.service";
import { loadEarModel, extractStableEarDescriptor } from "../services/ear-recognition.service";
import {
  FeatureDescriptor,
  ENROLLMENT_CAPTURES,
} from "../models/biometric-feature.model";

type CaptureStep =
  | "loading"
  | "waiting_face"
  | "waiting_blink"
  | "extracting_face"
  | "pose_transition"
  | "turn_head"
  | "extracting_ear"
  | "done"
  | "error";

interface BiometricCaptureFlowProps {
  mode: "enroll" | "verify";
  onComplete: (result: {
    faceDescriptors: FeatureDescriptor[];
    earDescriptor: FeatureDescriptor;
  }) => void;
  onError: (message: string) => void;
}

/** Eye Aspect Ratio — drops below ~0.2 during a blink.
 *  Formula and threshold from:
 *    T. Soukupová and J. Čech, "Real-Time Eye Blink Detection using Facial
 *    Landmarks", 21st Computer Vision Winter Workshop, 2016.
 *    https://vision.fe.uni-lj.si/cvww2016/proceedings/papers/05.pdf
 */
function eyeAspectRatio(eye: faceapi.Point[]): number {
  const v1 = Math.hypot(eye[1].x - eye[5].x, eye[1].y - eye[5].y);
  const v2 = Math.hypot(eye[2].x - eye[4].x, eye[2].y - eye[4].y);
  const h = Math.hypot(eye[0].x - eye[3].x, eye[0].y - eye[3].y);
  return h === 0 ? 1 : (v1 + v2) / (2 * h);
}

const BLINK_THRESHOLD = 0.22;
const BLINK_TIMEOUT_MS = 10000;
/** Time between enrolment captures — long enough for the user to physically
 *  move into a different lighting condition, not just adjust their head. */
const POSE_TRANSITION_MS = 6000;

/** Instructions shown for each enrolment capture. The three captures
 *  deliberately span different LIGHTING conditions as well as pose, because
 *  lighting drift is the dominant cause of cross-session verification
 *  failure (pose alone can't cover indoor vs. daylight). Each prompt offers
 *  a primary lighting instruction and a pose fallback for users who can't
 *  move. Users are never asked to turn left (reserved for ear capture). */
const ENROLLMENT_POSE_PROMPTS: { title: string; detail: string }[] = [
  {
    title: "Capture 1 of 3 \u2014 current position",
    detail: "Look straight at the camera in your current lighting. Hold still.",
  },
  {
    title: "Capture 2 of 3 \u2014 brighter light",
    detail: "Move toward a window or a brighter light source, then look at the camera again. If you can't move, tilt your chin DOWN slightly instead.",
  },
  {
    title: "Capture 3 of 3 \u2014 dimmer light",
    detail: "Now move to a dimmer spot, or turn away from the brightest light. If you can't move, tilt your chin UP slightly instead.",
  },
];

const VERIFY_PROMPT = {
  title: "Step 2 of 3: Capturing face",
  detail: "Hold still \u2014 capturing your facial features. This takes a few seconds.",
};

function BiometricCaptureFlow({ mode, onComplete, onError }: BiometricCaptureFlowProps) {
  const { theme } = useTheme();
  const [step, setStep] = useState<CaptureStep>("loading");
  const [faceDescriptors, setFaceDescriptors] = useState<FeatureDescriptor[]>([]);
  const [faceDetected, setFaceDetected] = useState(false);
  const [headTurnProgress, setHeadTurnProgress] = useState(0);
  const [poseCountdown, setPoseCountdown] = useState(0);

  const targetFaceCount = mode === "enroll" ? ENROLLMENT_CAPTURES : 1;

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

  // Face detection → blink detection → first face extraction.
  useEffect(() => {
    if (step !== "waiting_face" && step !== "waiting_blink") return;
    let running = true;

    if (step === "waiting_blink" && !blinkTimerRef.current) {
      blinkTimerRef.current = setTimeout(() => {
        if (running) setStep("extracting_face");
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

          if (step === "waiting_face") {
            setStep("waiting_blink");
            return;
          }

          const leftEye = detection.landmarks.getLeftEye();
          const rightEye = detection.landmarks.getRightEye();
          const ear = (eyeAspectRatio(leftEye) + eyeAspectRatio(rightEye)) / 2;

          if (ear < BLINK_THRESHOLD) {
            wasEyeClosedRef.current = true;
          } else if (wasEyeClosedRef.current) {
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
        const result = await extractStableFaceDescriptor(video, 5, 200);

        if (cancelled) return;

        if (!result) {
          // Retry — go back to face detection.
          setStep("waiting_face");
          setFaceDetected(false);
          return;
        }

        const nextDescriptors = [...faceDescriptors, result.descriptor];
        setFaceDescriptors(nextDescriptors);

        // Need more face captures? Show the pose prompt for the NEXT capture.
        if (nextDescriptors.length < targetFaceCount) {
          setStep("pose_transition");
        } else {
          setStep("turn_head");
        }
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

  // Pose-transition countdown between enrollment captures.
  useEffect(() => {
    if (step !== "pose_transition") return;

    setPoseCountdown(Math.ceil(POSE_TRANSITION_MS / 1000));
    const tick = setInterval(() => {
      setPoseCountdown((n) => Math.max(0, n - 1));
    }, 1000);
    const done = setTimeout(() => setStep("extracting_face"), POSE_TRANSITION_MS);

    return () => {
      clearInterval(tick);
      clearTimeout(done);
    };
  }, [step]);

  // Ear capture — wait 4 seconds for the user to turn, then capture.
  useEffect(() => {
    if (
      step !== "turn_head" ||
      faceDescriptors.length < targetFaceCount ||
      completedRef.current
    ) return;

    let elapsed = 0;
    const progressTick = setInterval(() => {
      elapsed++;
      setHeadTurnProgress(Math.min(100, Math.round((elapsed / 4) * 100)));
    }, 1000);

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
  }, [step, faceDescriptors.length]);

  // Ear extraction.
  useEffect(() => {
    if (step !== "extracting_ear" || faceDescriptors.length < targetFaceCount) return;
    let cancelled = false;

    (async () => {
      await new Promise((r) => setTimeout(r, 100));

      const video = camera.videoElRef.current;
      if (!video || cancelled) {
        onError("Camera not available for ear capture.");
        setStep("error");
        return;
      }

      try {
        const earResult = await extractStableEarDescriptor(video, 5, 300);
        if (cancelled) return;

        if (!earResult) {
          onError("Ear feature extraction returned no result.");
          setStep("error");
          return;
        }

        camera.stop();
        setStep("done");
        onComplete({ faceDescriptors, earDescriptor: earResult.descriptor });
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

  useEffect(() => () => cancelAnimationFrame(animFrameRef.current), []);

  // Dynamic instructions — depend on mode and current capture index.
  const capturesDone = faceDescriptors.length;
  const nextCaptureIdx = Math.min(capturesDone, targetFaceCount - 1);

  const INSTRUCTIONS: Record<CaptureStep, { title: string; detail: string }> = {
    loading: { title: "Preparing", detail: "Loading biometric models. This may take a moment on first use." },
    waiting_face: {
      title: mode === "enroll" ? "Step 1 of 3: Position your face" : "Step 1 of 3: Position your face",
      detail: "Centre your face within the oval guide. Make sure your face is well-lit and clearly visible.",
    },
    waiting_blink: { title: "Step 1 of 3: Liveness check", detail: "Face detected! Now blink naturally to prove you are a real person." },
    extracting_face: mode === "enroll"
      ? ENROLLMENT_POSE_PROMPTS[nextCaptureIdx] ?? VERIFY_PROMPT
      : VERIFY_PROMPT,
    pose_transition: {
      title: mode === "enroll"
        ? `Get ready for capture ${capturesDone + 1} of ${targetFaceCount}`
        : "Preparing next capture",
      detail: mode === "enroll"
        ? (ENROLLMENT_POSE_PROMPTS[nextCaptureIdx]?.detail ?? "")
        : "",
    },
    turn_head: { title: "Step 3 of 3: Show your ear", detail: "Turn your head to the LEFT to show your ear. Please make sure your ear is not covered by hair, headphones, or piercings. The camera will capture automatically in a few seconds." },
    extracting_ear: { title: "Step 3 of 3: Capturing ear", detail: "Hold still \u2014 capturing your ear features." },
    done: { title: "Complete", detail: "Both face and ear captured successfully." },
    error: { title: "Error", detail: "Something went wrong. Please try again." },
  };

  const info = INSTRUCTIONS[step];
  const stepNum = step === "loading" ? 0
    : (step === "waiting_face" || step === "waiting_blink") ? 1
    : (step === "extracting_face" || step === "pose_transition") ? 2
    : (step === "turn_head" || step === "extracting_ear") ? 3
    : 4;

  return (
    <div style={{ ...getCardStyle(theme), marginTop: "1rem" }}>
      <h2 style={{ fontSize: "1.1rem", fontWeight: 600, color: theme.colors.text.primary, margin: `0 0 ${theme.spacing.xs} 0` }}>
        {info.title}
      </h2>

      <p style={{ color: theme.colors.text.secondary || "#6b7280", fontSize: "0.9rem", lineHeight: 1.5, marginBottom: theme.spacing.md }}>
        {info.detail}
      </p>

      {/* Face-capture sub-progress (enrollment only) */}
      {mode === "enroll" && (step === "extracting_face" || step === "pose_transition") && (
        <div style={{
          display: "flex", gap: 6, marginBottom: theme.spacing.sm,
          justifyContent: "center",
        }}>
          {Array.from({ length: targetFaceCount }).map((_, i) => (
            <div key={i} style={{
              width: 22, height: 6, borderRadius: 3,
              background: i < capturesDone
                ? (theme.colors.status?.success || "#22c55e")
                : i === capturesDone
                  ? (theme.colors.primary || "#2563eb")
                  : "#e5e7eb",
              transition: "background 0.3s",
            }} />
          ))}
        </div>
      )}

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

      {step === "loading" && (
        <div style={{ textAlign: "center", padding: `${theme.spacing.lg} 0` }}>
          <p style={{ color: theme.colors.text.secondary || "#6b7280" }}>Initialising camera and models...</p>
        </div>
      )}

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

          {step === "extracting_face" && (
            <div style={{
              position: "absolute", bottom: 10, left: "50%", transform: "translateX(-50%)",
              background: "rgba(34,197,94,0.85)", color: "#fff",
              padding: "6px 14px", borderRadius: 12, fontSize: "0.8rem",
            }}>
              {mode === "enroll"
                ? `Capturing ${capturesDone + 1} of ${targetFaceCount}...`
                : "Capturing face... hold still"}
            </div>
          )}

          {step === "pose_transition" && (
            <div style={{
              position: "absolute", bottom: 10, left: "50%", transform: "translateX(-50%)",
              background: "rgba(37,99,235,0.85)", color: "#fff",
              padding: "6px 14px", borderRadius: 12, fontSize: "0.8rem",
              textAlign: "center", maxWidth: "85%",
            }}>
              Next capture in {poseCountdown}s — move to the new lighting
            </div>
          )}

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

          {step === "extracting_ear" && (
            <div style={{
              position: "absolute", bottom: 10, left: "50%", transform: "translateX(-50%)",
              background: "rgba(37,99,235,0.85)", color: "#fff",
              padding: "6px 14px", borderRadius: 12, fontSize: "0.8rem",
            }}>
              Capturing ear... hold still
            </div>
          )}

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

      {camera.error && (
        <p style={{ color: theme.colors.status?.error || "#ef4444", marginTop: theme.spacing.sm, fontSize: "0.85rem" }}>
          Camera error: {camera.error}
        </p>
      )}
    </div>
  );
}

export default BiometricCaptureFlow;
