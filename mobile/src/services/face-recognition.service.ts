/**
 * Face recognition using handcrafted features.
 *
 * Replaces the web frontend's face-api.js (TensorFlow.js) which cannot
 * run in React Native. Uses the same pipeline as ear recognition:
 * extract 512-d raw features from pixel data, project to 128-d with a
 * deterministic random projection matrix (different seed from ear).
 *
 * ML Kit provides the face bounding box for cropping. The handcrafted
 * features (pixel stats, histograms, gradients, LBP, plus landmark
 * geometry from ML Kit) are sufficient for same-person verification
 * with a 0.99 cosine similarity threshold.
 */

import { FeatureDescriptor, FeatureExtractionResult } from "../models/biometric-feature.model";
import {
  PixelBuffer,
  extractRawFeatures,
  buildProjectionMatrix,
  project,
} from "./feature-extraction.utils";

const FEATURE_DIM = 128;
const FACE_PROJECTION_SEED = 137; // different from ear seed (42)

let faceProjectionMatrix: Float32Array | null = null;

export function loadFaceModel(): void {
  faceProjectionMatrix = buildProjectionMatrix(FEATURE_DIM, FACE_PROJECTION_SEED);
}

/**
 * Extract a 128-d face descriptor from a cropped, resized 224x224 face image.
 * The caller is responsible for face detection (ML Kit) and cropping.
 */
export function extractFaceDescriptor(
  pixels: PixelBuffer,
): FeatureExtractionResult {
  if (!faceProjectionMatrix) {
    faceProjectionMatrix = buildProjectionMatrix(FEATURE_DIM, FACE_PROJECTION_SEED);
  }

  const raw = extractRawFeatures(pixels);
  const descriptor = project(raw, faceProjectionMatrix, FEATURE_DIM);

  return { descriptor, confidence: 1.0 };
}

/**
 * Multi-sample averaged face descriptor for stability.
 * Takes an array of pixel buffers captured at different moments.
 */
export function extractStableFaceDescriptor(
  frames: PixelBuffer[],
): FeatureExtractionResult | null {
  if (frames.length === 0) return null;

  const descriptors = frames.map((f) => extractFaceDescriptor(f).descriptor);

  const averaged = new Float32Array(FEATURE_DIM);
  for (const d of descriptors) {
    for (let j = 0; j < FEATURE_DIM; j++) averaged[j] += d[j];
  }
  for (let j = 0; j < FEATURE_DIM; j++) averaged[j] /= descriptors.length;

  // L2 normalise
  let norm = 0;
  for (let j = 0; j < FEATURE_DIM; j++) norm += averaged[j] * averaged[j];
  norm = Math.sqrt(norm) || 1;
  for (let j = 0; j < FEATURE_DIM; j++) averaged[j] /= norm;

  return { descriptor: averaged, confidence: 1.0 };
}
