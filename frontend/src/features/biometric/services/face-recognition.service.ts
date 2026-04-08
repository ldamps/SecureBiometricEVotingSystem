/**
 * Face recognition service using face-api.js (TensorFlow.js).
 *
 * Loads lightweight model variants (tiny face detector + 68-point landmarks
 * + 128-dimensional face descriptor network) and extracts a normalised
 * feature vector from a video frame.
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

/**
 * Detect a face in the given video element and return its 128-d descriptor.
 * Returns null when no face is detected with sufficient confidence.
 */
export async function extractFaceDescriptor(
  video: HTMLVideoElement,
): Promise<FeatureExtractionResult | null> {
  const detection = await faceapi
    .detectSingleFace(video, new faceapi.TinyFaceDetectorOptions({ scoreThreshold: 0.5 }))
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
 * stable reference template.  Used during enrollment to reduce noise.
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
