/**
 * Biometric feature models — shared between face and ear recognition.
 * Copied from the web frontend with identical thresholds and parameters.
 */

/** 128-dimensional feature descriptor. */
export type FeatureDescriptor = Float32Array;

export interface FeatureExtractionResult {
  descriptor: FeatureDescriptor;
  confidence: number;
}

export interface MatchResult {
  similarity: number;
  passed: boolean;
}

export interface MultiModalMatchResult {
  face: MatchResult;
  ear: MatchResult;
  overallPassed: boolean;
}

export interface QuantisationParams {
  numBins: number;
  rangeMin: number;
  rangeMax: number;
}

export interface EncryptedKeyCopy {
  salt: string;
  iv: string;
  encryptedPrivateKey: string;
}

export interface EncryptedKeyBundle {
  copies: EncryptedKeyCopy[];
  quantisationParams: QuantisationParams;
  /** @deprecated Single-copy fields for backward compatibility. */
  salt?: string;
  iv?: string;
  encryptedPrivateKey?: string;
}

export interface StoredBiometricData {
  voterId: string;
  faceTemplate: number[];
  earTemplate: number[];
  encryptedKeyBundle: EncryptedKeyBundle;
  enrolledAt: string;
}

/** Cosine similarity thresholds — both must pass (AND-fusion). */
export const BIOMETRIC_THRESHOLDS = {
  FACE: 0.99,
  EAR: 0.99,
} as const;

/** 8-bin quantisation for biometric-bound key derivation. */
export const DEFAULT_QUANTISATION_PARAMS: QuantisationParams = {
  numBins: 8,
  rangeMin: -1.0,
  rangeMax: 1.0,
};
