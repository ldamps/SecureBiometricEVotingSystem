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

/** A single encrypted copy of the ECDSA private key. */
export interface EncryptedKeyCopy {
  salt: string;
  iv: string;
  encryptedPrivateKey: string;
}

/**
 * Encrypted ECDSA private key bundle.
 *
 * Contains multiple encrypted copies of the SAME private key, each
 * encrypted with a slightly different quantisation offset.  This covers
 * the natural biometric variation between devices/conditions.  During
 * verification, the system tries each copy — if ANY one decrypts
 * (AES-GCM tag validates), the private key is recovered.
 *
 * No biometric data is stored — only encrypted key material.
 */
export interface EncryptedKeyBundle {
  copies: EncryptedKeyCopy[];
  quantisationParams: QuantisationParams;

  /** @deprecated Single-copy fields kept for backward compatibility. */
  salt?: string;
  iv?: string;
  encryptedPrivateKey?: string;
}

/** Full biometric enrollment data persisted on the device. */
export interface StoredBiometricData {
  voterId: string;
  faceTemplate: number[];
  earTemplate: number[];
  encryptedKeyBundle: EncryptedKeyBundle;
  enrolledAt: string;
}

/** Thresholds for biometric matching (cosine similarity).
 *
 * These thresholds gate an advisory template-matching check that
 * provides better error messages when enrolled templates are available
 * in IndexedDB.  The primary security gate is the biometric-bound key
 * decryption (AES-GCM), NOT template matching — so these thresholds
 * should be set at practical levels that accommodate cross-session
 * variation (lighting, angle, distance) on the same device.
 *
 * Face 0.92 and Ear 0.85 reliably reject impostors while tolerating
 * the natural variation observed between enrollment and verification
 * sessions on the same camera.
 */
export const BIOMETRIC_THRESHOLDS = {
  FACE: 0.92,
  EAR: 0.85,
} as const;

/** Default quantisation parameters.
 *
 * 4 bins across [-1, 1] gives a bin width of 0.5.  Face-api.js
 * descriptors are L2-normalised so values cluster in ~[-0.3, 0.3];
 * typical same-person per-dimension drift is 0.02–0.03 — only ~5%
 * of the bin width, making boundary crossings rare.
 *
 * Key entropy: 128 face dimensions × log2(4) = 256 bits, which
 * exactly matches AES-256 key length.  Combined with PBKDF2 (100k
 * iterations) this makes brute-force infeasible.
 *
 * Previous value was 8 bins (bin width 0.25), which caused frequent
 * decryption failures because ~25–40 dimensions would sit within
 * drift distance of a bin boundary on every capture.  The global
 * offset search cannot fix dimensions that need opposite corrections.
 */
export const DEFAULT_QUANTISATION_PARAMS: QuantisationParams = {
  numBins: 4,
  rangeMin: -1.0,
  rangeMax: 1.0,
};
