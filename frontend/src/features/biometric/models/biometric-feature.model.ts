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
 * Encrypted ECDSA private key bundle — two formats coexist.
 *
 * **v2 — fuzzy extractor (current):** a single `helper` string regenerates
 * a stable AES key from a noisy fresh biometric via Reed-Solomon error
 * correction. One-time enrollment survives cross-session drift (lighting,
 * angle, aging) for years. Identified by the presence of `helper`.
 *
 * **v1 — multi-copy offset search (legacy):** many encrypted copies of the
 * same private key under different quantisation offsets. Verification
 * tries each (copy, offset) pair. Less robust — drift on boundary-adjacent
 * dimensions causes uncorrectable failures. Identified by `copies`.
 *
 * No biometric data is stored in either format — only encrypted key
 * material (v1) or an information-theoretically hiding `helper` (v2).
 */
export interface EncryptedKeyBundle {
  /** Format discriminator. "fuzzy-extractor-rs-v2" for the new format;
   *  absent for legacy bundles. */
  format?: "fuzzy-extractor-rs-v2";

  // --- v2 fuzzy-extractor fields ---
  /** Hex-encoded RS codeword XOR quantised biometric (48 bytes). */
  helper?: string;
  /** Hex-encoded PBKDF2 salt (32 bytes). */
  salt?: string;
  /** Hex-encoded AES-GCM IV (12 bytes). */
  iv?: string;
  /** Hex-encoded AES-GCM ciphertext of the ECDSA private key. */
  encryptedPrivateKey?: string;

  // --- v1 legacy fields ---
  /** Legacy multi-copy offset scheme. */
  copies?: EncryptedKeyCopy[];

  /** Quantisation parameters used for feature binning. Shared by both
   *  formats (shape is identical). */
  quantisationParams?: QuantisationParams;
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

/** Legacy quantisation parameters (4 bins).
 *
 * Kept as the fallback for bundles that pre-date the quantisationParams
 * field so that old enrollments can still attempt verification.
 *
 * 4 bins across [-1, 1] places a boundary at 0.0 — right in the
 * densest part of the L2-normalised descriptor distribution.  ~27% of
 * dimensions land within drift distance of that boundary, and because
 * different dimensions need opposite corrections the global-offset
 * search cannot reliably recover them all.
 *
 * Previous value was 8 bins (bin width 0.25), which was even worse.
 */
export const DEFAULT_QUANTISATION_PARAMS: QuantisationParams = {
  numBins: 4,
  rangeMin: -1.0,
  rangeMax: 1.0,
};

/** Current enrollment quantisation parameters (5 bins).
 *
 * 5 bins across [-1, 1] gives a bin width of 0.4.  The nearest
 * boundaries to zero are at ±0.2 and ±0.6, which sit well outside
 * the dense centre of the descriptor distribution.  Only ~4.5% of
 * dimensions fall within drift distance (0.03) of a boundary —
 * a 6× improvement over the 4-bin layout.
 *
 * Key entropy: 128 × log2(5) ≈ 297 bits, more than sufficient for
 * AES-256.  Combined with PBKDF2 (100k iterations) brute-force
 * remains infeasible.
 */
export const ENROLLMENT_QUANTISATION_PARAMS: QuantisationParams = {
  numBins: 5,
  rangeMin: -1.0,
  rangeMax: 1.0,
};
