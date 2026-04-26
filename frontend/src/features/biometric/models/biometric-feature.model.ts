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
 * Encrypted ECDSA private key bundle — four formats coexist.
 *
 * **v4 — dual-modality fuzzy extractor (current):** binds BOTH face and
 * ear into the AES key. Two random messages `m_face` and `m_ear` are
 * each RS-encoded to codewords. `face_helpers[i] = c_face XOR b_face_i`
 * and `ear_helpers[i] = c_ear XOR b_ear_i`. Verification must RS-decode
 * one helper from EACH set; the AES key is derived from
 * `m_face || m_ear`, so failing either modality means no key. This makes
 * the ear an information-theoretic gate (not just an advisory cosine
 * check) and prevents wrong-ear acceptance even if the cosine layer is
 * bypassed.
 *
 * **v3 — face-only multi-helper fuzzy extractor:** a single `helpers`
 * array binding only the face descriptor. Re-enrolment required to
 * migrate to v4.
 *
 * **v2 — single-helper fuzzy extractor (legacy):** a single `helper`
 * string. Re-enrolment required to migrate to v4.
 *
 * **v1 — multi-copy offset search (legacy):** many encrypted copies of
 * the same private key under different quantisation offsets. Re-enrolment
 * required.
 */
export interface EncryptedKeyBundle {
  /** Format discriminator.
   *   "fuzzy-extractor-rs-v4" — dual-modality face + ear binding.
   *   "fuzzy-extractor-rs-v3" — face-only multi-helper (legacy).
   *   "fuzzy-extractor-rs-v2" — single-helper (legacy).
   *   absent — v1 legacy multi-copy format. */
  format?:
    | "fuzzy-extractor-rs-v4"
    | "fuzzy-extractor-rs-v3"
    | "fuzzy-extractor-rs-v2";

  // --- v4 dual-modality fields ---
  /** Hex-encoded RS codewords XOR quantised face descriptors (each 48 bytes). */
  face_helpers?: string[];
  /** Hex-encoded RS codewords XOR quantised ear descriptors (each 48 bytes). */
  ear_helpers?: string[];

  // --- v3 face-only multi-helper field ---
  /** Hex-encoded RS codewords XOR quantised face biometrics (each 48 bytes). */
  helpers?: string[];

  // --- v2 single-helper field (legacy, read-only) ---
  /** Hex-encoded RS codeword XOR quantised biometric (48 bytes). */
  helper?: string;

  // --- Shared v2/v3/v4 fields ---
  /** Hex-encoded PBKDF2 salt (32 bytes). */
  salt?: string;
  /** Hex-encoded AES-GCM IV (12 bytes). */
  iv?: string;
  /** Hex-encoded AES-GCM ciphertext of the ECDSA private key. */
  encryptedPrivateKey?: string;

  // --- v1 legacy fields ---
  /** Legacy multi-copy offset scheme. */
  copies?: EncryptedKeyCopy[];

  /** Quantisation parameters used for feature binning. Shared by all
   *  formats (shape is identical). */
  quantisationParams?: QuantisationParams;
}

/** Maximum number of helpers retained in a v3 bundle. Older helpers are
 *  dropped when adaptive update appends a new one at capacity — this keeps
 *  bundle size bounded while letting the helper set track current biometric
 *  variation over time. */
export const MAX_HELPERS = 8;

/** Number of pose/lighting captures taken during initial enrollment. */
export const ENROLLMENT_CAPTURES = 3;

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
 * Face 0.92 reliably rejects impostors against face-api.js's deep
 * descriptors.
 *
 * Ear 0.85 is calibrated for the central-crop HOG descriptor with
 * signed gradient orientations. The signed orientations are what
 * separate a left ear from a right ear: their helix curves sweep in
 * opposite directions, producing gradients pointing in opposite
 * directions along the curve. With unsigned orientations they would
 * look identical at the descriptor level; with signed orientations they
 * fall in different bins, so wrong-ear cosine drops well below
 * same-ear cosine.
 *
 * The cosine gate is the practical discriminator for the ear modality.
 * The fuzzy-extractor crypto gate behind it is permissive on same-ear
 * drift to avoid false rejections.
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

/** Ear-specific quantisation parameters.
 *
 * The ear descriptor uses the same wide [-1, 1] range as the face. An
 * earlier attempt to narrow this range to match the descriptor's
 * natural distribution gave better discrimination on paper but broke
 * legitimate matches: per-capture drift in HOG features routinely
 * crossed the tighter bin boundaries, pushing same-ear byte distance
 * past the Reed-Solomon error-correction budget. The wide range keeps
 * same-ear captures within budget; wrong-ear rejection is enforced by
 * the cosine-similarity gate (BIOMETRIC_THRESHOLDS.EAR) operating on
 * the central-crop HOG descriptor.
 */
export const EAR_QUANTISATION_PARAMS: QuantisationParams = {
  numBins: 5,
  rangeMin: -1.0,
  rangeMax: 1.0,
};
