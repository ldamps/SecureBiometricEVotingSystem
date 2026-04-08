/**
 * Biometric capture state machine.
 *
 * Orchestrates the face → blink → ear capture flow, matching the
 * web frontend's BiometricCaptureFlow.tsx logic.
 *
 * States: loading → waiting_face → waiting_blink → extracting_face
 *         → turn_head → extracting_ear → done
 */

import { useState, useRef, useCallback } from "react";
import { FeatureDescriptor } from "../models/biometric-feature.model";
import { PixelBuffer } from "../services/feature-extraction.utils";
import { extractStableFaceDescriptor } from "../services/face-recognition.service";
import { extractStableEarDescriptor } from "../services/ear-recognition.service";

export type CaptureStep =
  | "loading"
  | "waiting_face"
  | "waiting_blink"
  | "extracting_face"
  | "turn_head"
  | "extracting_ear"
  | "done"
  | "error";

export interface CaptureResult {
  faceDescriptor: FeatureDescriptor;
  earDescriptor: FeatureDescriptor;
}

const FACE_SAMPLES = 5;   // enrollment samples
const VERIFY_SAMPLES = 3; // verification samples
const EAR_SAMPLES = 5;
const VERIFY_EAR_SAMPLES = 3;
const SAMPLE_DELAY_MS = 250;

export function useBiometricCapture(mode: "enroll" | "verify") {
  const [step, setStep] = useState<CaptureStep>("loading");
  const [error, setError] = useState<string | null>(null);
  const [faceDescriptor, setFaceDescriptor] = useState<FeatureDescriptor | null>(null);
  const [result, setResult] = useState<CaptureResult | null>(null);

  const faceFramesRef = useRef<PixelBuffer[]>([]);
  const earFramesRef = useRef<PixelBuffer[]>([]);
  const blinkDetectedRef = useRef(false);

  const faceSamples = mode === "enroll" ? FACE_SAMPLES : VERIFY_SAMPLES;
  const earSamples = mode === "enroll" ? EAR_SAMPLES : VERIFY_EAR_SAMPLES;

  /** Called by the screen when models are loaded and camera is ready. */
  const onReady = useCallback(() => {
    setStep("waiting_face");
  }, []);

  /** Called when ML Kit detects a face in the frame. */
  const onFaceDetected = useCallback(() => {
    setStep((prev) => (prev === "waiting_face" ? "waiting_blink" : prev));
  }, []);

  /** Called when blink detection succeeds (EAR drop below threshold then recover). */
  const onBlinkDetected = useCallback(() => {
    blinkDetectedRef.current = true;
    setStep("extracting_face");
  }, []);

  /** Called with captured face frames for descriptor extraction. */
  const onFaceFramesCaptured = useCallback(
    async (frames: PixelBuffer[]) => {
      try {
        const result = extractStableFaceDescriptor(frames);
        if (!result) {
          setStep("waiting_face"); // retry
          return;
        }
        setFaceDescriptor(result.descriptor);
        setStep("turn_head");
      } catch (err: any) {
        setError(err.message || "Face extraction failed.");
        setStep("error");
      }
    },
    [],
  );

  /** Called with captured ear frames for descriptor extraction. */
  const onEarFramesCaptured = useCallback(
    async (frames: PixelBuffer[]) => {
      if (!faceDescriptor) {
        setError("Face descriptor missing.");
        setStep("error");
        return;
      }
      try {
        const earResult = extractStableEarDescriptor(frames);
        if (!earResult) {
          setError("Ear feature extraction returned no result.");
          setStep("error");
          return;
        }

        const captureResult: CaptureResult = {
          faceDescriptor,
          earDescriptor: earResult.descriptor,
        };
        setResult(captureResult);
        setStep("done");
      } catch (err: any) {
        setError(err.message || "Ear extraction failed.");
        setStep("error");
      }
    },
    [faceDescriptor],
  );

  const reset = useCallback(() => {
    setStep("loading");
    setError(null);
    setFaceDescriptor(null);
    setResult(null);
    faceFramesRef.current = [];
    earFramesRef.current = [];
    blinkDetectedRef.current = false;
  }, []);

  return {
    step,
    error,
    result,
    faceSamples,
    earSamples,
    sampleDelayMs: SAMPLE_DELAY_MS,
    onReady,
    onFaceDetected,
    onBlinkDetected,
    onFaceFramesCaptured,
    onEarFramesCaptured,
    reset,
  };
}
