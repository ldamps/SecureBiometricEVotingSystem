/**
 * Biometric matching using cosine similarity.
 *
 * Both face and ear modalities must independently pass their threshold
 * for the overall match to succeed (AND-fusion).
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

/**
 * Compare a fresh face descriptor against multiple enrolled descriptors
 * and return the best cosine. Used when enrolment captured several
 * descriptors under varied lighting/pose — same person under conditions
 * close to *any* of them passes, while a different person remains far
 * from all of them.
 */
export function matchFaceAgainstSet(
  probe: FeatureDescriptor,
  references: FeatureDescriptor[],
): MatchResult {
  if (references.length === 0) {
    return { similarity: 0, passed: false };
  }
  let best = -1;
  for (const ref of references) {
    const sim = cosineSimilarity(probe, ref);
    if (sim > best) best = sim;
  }
  return { similarity: best, passed: best >= BIOMETRIC_THRESHOLDS.FACE };
}

export function matchEar(
  probe: FeatureDescriptor,
  reference: FeatureDescriptor,
): MatchResult {
  const similarity = cosineSimilarity(probe, reference);
  return { similarity, passed: similarity >= BIOMETRIC_THRESHOLDS.EAR };
}

/**
 * AND-fusion: both modalities must pass independently.
 *
 * `faceRef` accepts either a single descriptor (legacy) or an array of
 * enrolled descriptors. With an array, the best cosine across the set
 * is used — see `matchFaceAgainstSet` for rationale.
 */
export function matchBoth(
  faceProbe: FeatureDescriptor,
  faceRef: FeatureDescriptor | FeatureDescriptor[],
  earProbe: FeatureDescriptor,
  earRef: FeatureDescriptor,
): MultiModalMatchResult {
  const face = Array.isArray(faceRef)
    ? matchFaceAgainstSet(faceProbe, faceRef)
    : matchFace(faceProbe, faceRef);
  const ear = matchEar(earProbe, earRef);
  return { face, ear, overallPassed: face.passed && ear.passed };
}
