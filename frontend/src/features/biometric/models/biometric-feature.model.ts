/**
 * TypeScript models for the multi-modal biometric system.
 *
 * Face + ear feature vectors are extracted on-device, matched locally,
 * and used to derive a biometric-bound AES-GCM key that encrypts the
 * ECDSA signing key.  No biometric data ever leaves the device.
 */

/** 128-dimensional feature descriptor produced by an ML model. */
export type FeatureDescriptor = Float32Array;

/** Result of extracting features from a single image frame. */
export interface FeatureExtractionResult {
  descriptor: FeatureDescriptor;
  confidence: number;
}

/** Result of comparing a probe descriptor against a reference. */
export interface MatchResult {
  similarity: number;
  passed: boolean;
}

/** Combined result of matching both face and ear modalities. */
export interface MultiModalMatchResult {
  face: MatchResult;
  ear: MatchResult;
  overallPassed: boolean;
}

/** Parameters controlling the quantisation of feature vectors into bins. */
export interface QuantisationParams {
  numBins: number;
  rangeMin: number;
  rangeMax: number;
}

/** Encrypted ECDSA private key bundle stored in IndexedDB. */
export interface EncryptedKeyBundle {
  salt: string;
  iv: string;
  encryptedPrivateKey: string;
  quantisationParams: QuantisationParams;
}

/** Full biometric enrollment data persisted on the device. */
export interface StoredBiometricData {
  voterId: string;
  faceTemplate: number[];
  earTemplate: number[];
  encryptedKeyBundle: EncryptedKeyBundle;
  enrolledAt: string;
}

/** Thresholds for biometric matching (cosine similarity). */
export const BIOMETRIC_THRESHOLDS = {
  FACE: 0.95,
  EAR: 0.95,
} as const;

/** Default quantisation parameters.
 *
 * Using 2 wide bins (binary quantisation) maximises tolerance to the
 * natural variation between biometric captures while still producing a
 * key that is bound to the person's features.  Each dimension maps to
 * either 0 or 1 based on whether it falls below or above the midpoint.
 */
export const DEFAULT_QUANTISATION_PARAMS: QuantisationParams = {
  numBins: 2,
  rangeMin: -1.0,
  rangeMax: 1.0,
};
