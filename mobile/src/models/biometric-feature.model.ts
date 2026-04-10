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

/** Cosine similarity thresholds — both must pass (AND-fusion).
 * Advisory only; the real security gate is AES-GCM key decryption. */
export const BIOMETRIC_THRESHOLDS = {
  FACE: 0.92,
  EAR: 0.85,
} as const;

/** 4-bin quantisation for biometric-bound key derivation.
 * 128 dims × log2(4) = 256-bit key entropy (AES-256 strength). */
export const DEFAULT_QUANTISATION_PARAMS: QuantisationParams = {
  numBins: 4,
  rangeMin: -1.0,
  rangeMax: 1.0,
};
