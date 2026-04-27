/**
 * Face recognition service using face-api.js (TensorFlow.js).
 *
 * Loads lightweight model variants (tiny face detector + 68-point landmarks
 * + 128-dimensional face descriptor network) and extracts a normalised
 * feature vector from a video frame.
 *
 * References:
 *   - V. Mühler, "face-api.js: JavaScript API for face detection and face
 *     recognition in the browser implemented on top of the tensorflow.js
 *     core API", 2018.
 *     https://github.com/justadudewhohacks/face-api.js
 *   - F. Schroff, D. Kalenichenko and J. Philbin, "FaceNet: A Unified
 *     Embedding for Face Recognition and Clustering", CVPR 2015 — the
 *     triplet-loss embedding strategy underpinning the descriptor net.
 *     https://arxiv.org/abs/1503.03832
 *   - K. He, X. Zhang, S. Ren and J. Sun, "Deep Residual Learning for
 *     Image Recognition", CVPR 2016 — the ResNet-34 backbone of
 *     faceRecognitionNet.
 *     https://arxiv.org/abs/1512.03385
 *   - J. Redmon and A. Farhadi, "YOLO9000: Better, Faster, Stronger",
 *     CVPR 2017 — basis for the Tiny Face Detector.
 *     https://arxiv.org/abs/1612.08242
 */

import * as faceapi from "face-api.js";
import { FeatureDescriptor, FeatureExtractionResult } from "../models/biometric-feature.model";

const MODEL_URL = "/models/face-api";

let modelsLoaded = false;

/** L2-normalise a feature vector to unit length. */
function l2Normalise(v: Float32Array): Float32Array {
  let norm = 0;
  for (let i = 0; i < v.length; i++) norm += v[i] * v[i];
  norm = Math.sqrt(norm) || 1;
  const out = new Float32Array(v.length);
  for (let i = 0; i < v.length; i++) out[i] = v[i] / norm;
  return out;
}

export async function loadFaceModels(): Promise<void> {
  if (modelsLoaded) return;
  await Promise.all([
    faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
    faceapi.nets.faceLandmark68TinyNet.loadFromUri(MODEL_URL),
    faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
  ]);
  modelsLoaded = true;
}

/** Tighter detection-confidence threshold than face-api.js's default
 *  (0.4). Lower thresholds let through marginal detections that produce
 *  noisier descriptors, which in turn produces unstable cosine values
 *  at verification. 0.5 is a deliberate trade — marginally fewer
 *  detections under poor lighting, but the ones that pass are
 *  meaningfully more reliable. */
const DETECTION_SCORE_THRESHOLD = 0.5;

/** Sanity threshold for *internal* consistency of the 5-frame capture.
 *  Two consecutive samples of the same face should pass this comfortably;
 *  if any pair drops below it, the camera is probably seeing different
 *  things mid-capture (frame change, multiple faces in view) and the
 *  averaged descriptor is unreliable. Reject in that case. */
const INTRA_CAPTURE_MIN_COSINE = 0.85;

function cosineUnit(a: Float32Array, b: Float32Array): number {
  let dot = 0;
  for (let i = 0; i < a.length; i++) dot += a[i] * b[i];
  return dot;
}

/**
 * Detect a face in the given video element and return its 128-d descriptor.
 * Returns null when no face is detected with sufficient confidence.
 */
export async function extractFaceDescriptor(
  video: HTMLVideoElement,
): Promise<FeatureExtractionResult | null> {
  const detection = await faceapi
    .detectSingleFace(
      video,
      new faceapi.TinyFaceDetectorOptions({ scoreThreshold: DETECTION_SCORE_THRESHOLD }),
    )
    .withFaceLandmarks(true)
    .withFaceDescriptor();

  if (!detection) return null;

  // L2-normalise the raw descriptor so cosine similarity thresholds
  // are meaningful and consistent across different lighting/cameras.
  const raw = detection.descriptor as FeatureDescriptor;
  const normalised = l2Normalise(raw);

  return {
    descriptor: normalised,
    confidence: detection.detection.score,
  };
}

/**
 * Capture multiple frames, average the descriptors, and return a more
 * stable reference template. Used during enrollment to reduce noise
 * and during verification to suppress per-frame jitter.
 *
 * Rejects the capture (returns null) if the per-frame descriptors are
 * mutually inconsistent — that's a signal that the camera saw two
 * different faces or a frame change during the 1-second capture
 * window, in which case averaging would silently produce a meaningless
 * blended descriptor.
 */
export async function extractStableFaceDescriptor(
  video: HTMLVideoElement,
  numSamples: number = 5,
  delayMs: number = 300,
): Promise<FeatureExtractionResult | null> {
  const descriptors: Float32Array[] = [];
  let totalConfidence = 0;

  for (let i = 0; i < numSamples; i++) {
    const result = await extractFaceDescriptor(video);
    if (result) {
      descriptors.push(result.descriptor);
      totalConfidence += result.confidence;
    }
    if (i < numSamples - 1) {
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }

  if (descriptors.length === 0) return null;

  // Internal consistency check — every pair of samples should be very
  // similar. If the camera switched scenes mid-capture, the averaged
  // descriptor is meaningless.
  if (descriptors.length >= 2) {
    let minPair = 1;
    for (let i = 0; i < descriptors.length; i++) {
      for (let j = i + 1; j < descriptors.length; j++) {
        const sim = cosineUnit(descriptors[i], descriptors[j]);
        if (sim < minPair) minPair = sim;
      }
    }
    if (minPair < INTRA_CAPTURE_MIN_COSINE) {
      // eslint-disable-next-line no-console
      console.warn(
        `[face] rejecting capture — inter-frame cosine ${minPair.toFixed(3)} ` +
          `below ${INTRA_CAPTURE_MIN_COSINE} (saw inconsistent faces during the capture window)`,
      );
      return null;
    }
  }

  // Average all captured descriptors and re-normalise for stability.
  const averaged = new Float32Array(128);
  for (const d of descriptors) {
    for (let j = 0; j < 128; j++) averaged[j] += d[j];
  }
  for (let j = 0; j < 128; j++) averaged[j] /= descriptors.length;
  const normalised = l2Normalise(averaged);

  return {
    descriptor: normalised,
    confidence: totalConfidence / descriptors.length,
  };
}
