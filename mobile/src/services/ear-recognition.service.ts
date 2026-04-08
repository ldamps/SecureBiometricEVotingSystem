/**
 * Ear recognition — ported from the web frontend.
 *
 * Uses the same handcrafted feature extraction pipeline (pixel stats,
 * histograms, gradients, LBP) with the same projection seed (42)
 * to produce identical 128-d descriptors as the web version.
 */

import { FeatureDescriptor, FeatureExtractionResult } from "../models/biometric-feature.model";
import {
  PixelBuffer,
  extractRawFeatures,
  buildProjectionMatrix,
  project,
} from "./feature-extraction.utils";

const FEATURE_DIM = 128;
const EAR_PROJECTION_SEED = 42; // same as web frontend

let earProjectionMatrix: Float32Array | null = null;

export function loadEarModel(): void {
  earProjectionMatrix = buildProjectionMatrix(FEATURE_DIM, EAR_PROJECTION_SEED);
}

/**
 * Extract a 128-d ear descriptor from a 224x224 pixel buffer.
 */
export function extractEarDescriptor(
  pixels: PixelBuffer,
): FeatureExtractionResult {
  if (!earProjectionMatrix) {
    earProjectionMatrix = buildProjectionMatrix(FEATURE_DIM, EAR_PROJECTION_SEED);
  }

  const raw = extractRawFeatures(pixels);
  const descriptor = project(raw, earProjectionMatrix, FEATURE_DIM);

  return { descriptor, confidence: 1.0 };
}

/**
 * Multi-sample averaged ear descriptor for stability.
 */
export function extractStableEarDescriptor(
  frames: PixelBuffer[],
): FeatureExtractionResult | null {
  if (frames.length === 0) return null;

  const descriptors = frames.map((f) => extractEarDescriptor(f).descriptor);

  const averaged = new Float32Array(FEATURE_DIM);
  for (const d of descriptors) {
    for (let j = 0; j < FEATURE_DIM; j++) averaged[j] += d[j];
  }
  for (let j = 0; j < FEATURE_DIM; j++) averaged[j] /= descriptors.length;

  let norm = 0;
  for (let j = 0; j < FEATURE_DIM; j++) norm += averaged[j] * averaged[j];
  norm = Math.sqrt(norm) || 1;
  for (let j = 0; j < FEATURE_DIM; j++) averaged[j] /= norm;

  return { descriptor: averaged, confidence: 1.0 };
}
