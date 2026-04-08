/**
 * Biometric matching using cosine similarity.
 * Copied verbatim from the web frontend — pure Float32Array math.
 */

import {
  FeatureDescriptor,
  MatchResult,
  MultiModalMatchResult,
  BIOMETRIC_THRESHOLDS,
} from "../models/biometric-feature.model";

export function cosineSimilarity(a: FeatureDescriptor, b: FeatureDescriptor): number {
  let dot = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  const denom = Math.sqrt(normA) * Math.sqrt(normB);
  return denom === 0 ? 0 : dot / denom;
}

export function matchFace(
  probe: FeatureDescriptor,
  reference: FeatureDescriptor,
): MatchResult {
  const similarity = cosineSimilarity(probe, reference);
  return { similarity, passed: similarity >= BIOMETRIC_THRESHOLDS.FACE };
}

export function matchEar(
  probe: FeatureDescriptor,
  reference: FeatureDescriptor,
): MatchResult {
  const similarity = cosineSimilarity(probe, reference);
  return { similarity, passed: similarity >= BIOMETRIC_THRESHOLDS.EAR };
}

/** AND-fusion: both modalities must pass independently. */
export function matchBoth(
  faceProbe: FeatureDescriptor,
  faceRef: FeatureDescriptor,
  earProbe: FeatureDescriptor,
  earRef: FeatureDescriptor,
): MultiModalMatchResult {
  const face = matchFace(faceProbe, faceRef);
  const ear = matchEar(earProbe, earRef);
  return { face, ear, overallPassed: face.passed && ear.passed };
}
