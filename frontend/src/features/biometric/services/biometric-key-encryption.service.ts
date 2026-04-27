/**
 * Dual-modality biometric-bound key encryption (v4).
 *
 * Both face AND ear are required cryptographically — losing either one
 * means the AES key cannot be reconstructed, regardless of any
 * client-side similarity gate. This closes the wrong-ear acceptance hole
 * that v3 left open (v3 only bound the face into the key; the ear was
 * an advisory cosine check).
 *
 * Design — dual-modality multi-helper code-offset fuzzy extractor:
 *
 *   Enrollment (N face captures, 1 ear capture):
 *     1. Pick two independent uniformly random 16-byte messages
 *        m_face, m_ear.
 *     2. RS-encode each → codewords c_face, c_ear (each 48 bytes).
 *     3. For each face capture i: face_helpers[i] = c_face XOR b_face_i.
 *     4. For the ear capture: ear_helpers[0] = c_ear XOR b_ear.
 *     5. Combined secret S = m_face || m_ear (32 bytes).
 *     6. Derive AES-256 key K = PBKDF2(S, salt, 100k iterations).
 *     7. Encrypt the ECDSA signing key under K with AES-GCM.
 *
 *   Verification:
 *     1. Capture fresh face descriptor b_face' and ear descriptor b_ear'.
 *     2. Find the first face_helper that RS-decodes against b_face'
 *        → recover m_face.
 *     3. Find the first ear_helper that RS-decodes against b_ear'
 *        → recover m_ear.
 *     4. If EITHER set fails to decode, abort — no key is recoverable.
 *     5. Reconstruct S = m_face || m_ear, derive K, decrypt private key.
 *     6. AES-GCM tag validates the recovery was correct.
 *
 *   Adaptive update (after successful verification):
 *     1. Recompute c_face = rsEncode(m_face), c_ear = rsEncode(m_ear).
 *     2. Append fresh helpers c_face XOR b_face' and c_ear XOR b_ear'.
 *     3. Drop oldest helper per modality if at capacity.
 *
 * Why both modalities matter cryptographically:
 *   In v3 the ear contributed only to the cosine-similarity gate, which
 *   runs in the PWA's JavaScript context — anyone who can run JS in
 *   that origin can skip it. v4 makes the ear part of the key-derivation
 *   maths: a wrong-ear capture XOR'd against ear_helpers produces a
 *   noisy-codeword too far from any RS codeword to correct, so m_ear is
 *   never recovered, the combined secret is wrong, AES-GCM rejects the
 *   ciphertext, and the private key stays sealed.
 *
 * Security notes:
 *   - face_helpers and ear_helpers each independently XOR a random
 *     codeword with a high-min-entropy biometric → information-
 *     theoretically hiding under standard fuzzy-extractor assumptions.
 *   - Adding more helpers does not reduce entropy of either m_* — they
 *     all mask the same per-modality codeword.
 *   - Combined secret is 32 bytes, far beyond what AES-256 needs.
 *   - PBKDF2 (100k iterations) makes any residual entropy loss
 *     impractical to brute-force.
 *
 * References:
 *   - Y. Dodis, L. Reyzin and A. Smith, "Fuzzy Extractors: How to Generate
 *     Strong Keys from Biometrics and Other Noisy Data", SIAM J. Computing,
 *     vol. 38, no. 1, 2008 (extended version of Eurocrypt 2004). The
 *     code-offset construction used here (helper = RS(m) XOR b) is from
 *     Section 5 of that paper.
 *     https://www.cs.bu.edu/~reyzin/papers/fuzzy.pdf
 *   - B. Kaliski, "PKCS #5: Password-Based Cryptography Specification
 *     Version 2.0", RFC 2898, 2000 (PBKDF2).
 *     https://datatracker.ietf.org/doc/html/rfc2898
 *   - M. Dworkin, "Recommendation for Block Cipher Modes of Operation:
 *     Galois/Counter Mode (GCM) and GMAC", NIST SP 800-38D, 2007.
 *     https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38d.pdf
 *   - NIST, "Digital Signature Standard (DSS)", FIPS PUB 186-4, 2013
 *     (ECDSA over P-256).
 *     https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.186-4.pdf
 */

import {
  FeatureDescriptor,
  EncryptedKeyBundle,
  QuantisationParams,
  EAR_QUANTISATION_PARAMS,
  ENROLLMENT_QUANTISATION_PARAMS,
  MAX_HELPERS,
} from "../models/biometric-feature.model";
import { rsEncode, rsDecode, RS_PARAMS } from "./reed-solomon.service";

const DESCRIPTOR_LEN = 128;

/** Gray-code mapping for 5 bins — adjacent bins differ by exactly 1 bit,
 *  so a single-bin drift at verification time flips at most 1 bit in the
 *  packed representation. (Bins 0..4 → 000, 001, 011, 010, 110.) */
const GRAY_5_BIN = [0b000, 0b001, 0b011, 0b010, 0b110];

// ----- Hex helpers -----
function toHex(buf: ArrayBuffer): string {
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function fromHex(hex: string): Uint8Array {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < bytes.length; i++) {
    bytes[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  }
  return bytes;
}

// ----- Quantisation + bit packing -----

function quantiseGrayCoded(
  descriptor: FeatureDescriptor,
  params: QuantisationParams,
): number[] {
  if (params.numBins !== 5) {
    throw new Error(
      `Quantisation must use 5 bins for fuzzy extractor (got ${params.numBins}).`,
    );
  }
  const { numBins, rangeMin, rangeMax } = params;
  const binWidth = (rangeMax - rangeMin) / numBins;
  const out: number[] = new Array(descriptor.length);
  for (let i = 0; i < descriptor.length; i++) {
    const clamped = Math.max(rangeMin, Math.min(rangeMax - 1e-9, descriptor[i]));
    let bin = Math.floor((clamped - rangeMin) / binWidth);
    if (bin < 0) bin = 0;
    if (bin >= numBins) bin = numBins - 1;
    out[i] = GRAY_5_BIN[bin];
  }
  return out;
}

function packBits3(values: number[]): Uint8Array {
  if (values.length !== DESCRIPTOR_LEN) {
    throw new Error(`Expected ${DESCRIPTOR_LEN} values, got ${values.length}.`);
  }
  const out = new Uint8Array(RS_PARAMS.n);
  let bitPos = 0;
  for (let i = 0; i < values.length; i++) {
    const v = values[i] & 0b111;
    for (let b = 0; b < 3; b++) {
      if ((v >> b) & 1) {
        out[Math.floor(bitPos / 8)] |= 1 << (bitPos % 8);
      }
      bitPos++;
    }
  }
  return out;
}

function descriptorToBytes(
  descriptor: FeatureDescriptor,
  params: QuantisationParams,
): Uint8Array {
  if (descriptor.length !== DESCRIPTOR_LEN) {
    throw new Error(
      `Expected ${DESCRIPTOR_LEN}-dim descriptor, got ${descriptor.length}.`,
    );
  }
  return packBits3(quantiseGrayCoded(descriptor, params));
}

// ----- AES key derivation -----

async function deriveAesKey(
  message: Uint8Array,
  salt: Uint8Array,
): Promise<CryptoKey> {
  const keyMaterial = await crypto.subtle.importKey(
    "raw",
    message.buffer.slice(message.byteOffset, message.byteOffset + message.byteLength) as ArrayBuffer,
    "PBKDF2",
    false,
    ["deriveKey"],
  );
  return crypto.subtle.deriveKey(
    {
      name: "PBKDF2",
      salt: salt.buffer.slice(salt.byteOffset, salt.byteOffset + salt.byteLength) as ArrayBuffer,
      iterations: 100_000,
      hash: "SHA-256",
    },
    keyMaterial,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"],
  );
}

/** Build the per-modality helper from a fresh descriptor and a known
 *  random message. */
function buildHelper(
  descriptor: FeatureDescriptor,
  message: Uint8Array,
  params: QuantisationParams,
): string {
  const b = descriptorToBytes(descriptor, params);
  const c = rsEncode(message, RS_PARAMS.nsym);
  const helper = new Uint8Array(RS_PARAMS.n);
  for (let i = 0; i < RS_PARAMS.n; i++) helper[i] = c[i] ^ b[i];
  return toHex(helper.buffer as ArrayBuffer);
}

/** Try every helper in `helperHexes` against descriptor `b'`. Returns the
 *  recovered message of the first helper that RS-decodes, or null. */
function recoverMessageFromHelpers(
  helperHexes: string[],
  bPrime: Uint8Array,
): Uint8Array | null {
  for (const helperHex of helperHexes) {
    const helper = fromHex(helperHex);
    if (helper.length !== RS_PARAMS.n) continue;
    const noisyC = new Uint8Array(RS_PARAMS.n);
    for (let i = 0; i < RS_PARAMS.n; i++) noisyC[i] = helper[i] ^ bPrime[i];
    const corrected = rsDecode(noisyC, RS_PARAMS.nsym);
    if (corrected !== null) return corrected.slice(0, RS_PARAMS.k);
  }
  return null;
}

// ----- Public enrollment + verification API -----

/**
 * Generate an ECDSA keypair and encrypt the private key under a key
 * derived from BOTH face and ear biometrics. Both modalities must be
 * present at verification — neither alone can recover the key.
 */
export async function generateAndEncryptKeyPair(
  faceDescriptors: FeatureDescriptor[],
  earDescriptor: FeatureDescriptor,
  params: QuantisationParams = ENROLLMENT_QUANTISATION_PARAMS,
): Promise<{ publicKeyPem: string; encryptedBundle: EncryptedKeyBundle }> {
  if (faceDescriptors.length === 0) {
    throw new Error("At least one enrolment face descriptor is required.");
  }

  // 1. Two independent random messages — one per modality.
  const mFace = crypto.getRandomValues(new Uint8Array(RS_PARAMS.k));
  const mEar = crypto.getRandomValues(new Uint8Array(RS_PARAMS.k));

  // 2. Build per-modality helpers.
  const faceHelpers: string[] = faceDescriptors.map((d) =>
    buildHelper(d, mFace, params),
  );
  // Ear uses its own quantisation range matched to the HOG descriptor's
  // tighter L2-normalised distribution. See EAR_QUANTISATION_PARAMS.
  const earHelpers: string[] = [
    buildHelper(earDescriptor, mEar, EAR_QUANTISATION_PARAMS),
  ];

  // 3. Combined secret seeds the AES key.
  const combined = new Uint8Array(mFace.length + mEar.length);
  combined.set(mFace, 0);
  combined.set(mEar, mFace.length);

  const salt = crypto.getRandomValues(new Uint8Array(32));
  const aesKey = await deriveAesKey(combined, salt);

  // 4. Generate the ECDSA keypair and encrypt the private key.
  const keyPair = await crypto.subtle.generateKey(
    { name: "ECDSA", namedCurve: "P-256" },
    true,
    ["sign", "verify"],
  );
  const privateKeyDer = await crypto.subtle.exportKey("pkcs8", keyPair.privateKey);

  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: iv.buffer as ArrayBuffer },
    aesKey,
    privateKeyDer,
  );

  const publicKeyDer = await crypto.subtle.exportKey("spki", keyPair.publicKey);
  const publicKeyBase64 = btoa(
    String.fromCharCode.apply(null, Array.from(new Uint8Array(publicKeyDer))),
  );
  const publicKeyPem =
    "-----BEGIN PUBLIC KEY-----\n" +
    publicKeyBase64.match(/.{1,64}/g)!.join("\n") +
    "\n-----END PUBLIC KEY-----";

  return {
    publicKeyPem,
    encryptedBundle: {
      format: "fuzzy-extractor-rs-v4",
      face_helpers: faceHelpers,
      ear_helpers: earHelpers,
      salt: toHex(salt.buffer as ArrayBuffer),
      iv: toHex(iv.buffer as ArrayBuffer),
      encryptedPrivateKey: toHex(ciphertext),
      quantisationParams: params,
    },
  };
}

/**
 * Recover the ECDSA private key from a fresh dual-modality biometric
 * capture. Requires v4 bundle. Returns the private key plus both
 * recovered messages (needed by `appendAdaptiveHelper`).
 */
export async function decryptPrivateKey(
  faceDescriptor: FeatureDescriptor,
  earDescriptor: FeatureDescriptor,
  bundle: EncryptedKeyBundle,
): Promise<{
  privateKey: CryptoKey;
  recoveredFaceMessage: Uint8Array;
  recoveredEarMessage: Uint8Array;
}> {
  if (
    bundle.format !== "fuzzy-extractor-rs-v4" ||
    !bundle.face_helpers ||
    bundle.face_helpers.length === 0 ||
    !bundle.ear_helpers ||
    bundle.ear_helpers.length === 0 ||
    !bundle.salt ||
    !bundle.iv ||
    !bundle.encryptedPrivateKey
  ) {
    throw new Error(
      "Legacy enrollment format. Please re-enroll once on this device to " +
        "migrate to the dual-modality (face + ear) cryptographic binding.",
    );
  }

  const params = bundle.quantisationParams ?? ENROLLMENT_QUANTISATION_PARAMS;
  const bFace = descriptorToBytes(faceDescriptor, params);
  const bEar = descriptorToBytes(earDescriptor, EAR_QUANTISATION_PARAMS);

  const recoveredFaceMessage = recoverMessageFromHelpers(bundle.face_helpers, bFace);
  if (recoveredFaceMessage === null) {
    throw new Error(
      "Face biometric drift exceeds error-correction capacity for every " +
        "stored helper. Check lighting, angle, and camera framing.",
    );
  }

  const recoveredEarMessage = recoverMessageFromHelpers(bundle.ear_helpers, bEar);
  if (recoveredEarMessage === null) {
    throw new Error(
      "Ear biometric drift exceeds error-correction capacity for every " +
        "stored helper. Ensure the ear is fully in frame and unobstructed.",
    );
  }

  const combined = new Uint8Array(recoveredFaceMessage.length + recoveredEarMessage.length);
  combined.set(recoveredFaceMessage, 0);
  combined.set(recoveredEarMessage, recoveredFaceMessage.length);

  const salt = fromHex(bundle.salt);
  const iv = fromHex(bundle.iv);
  const ciphertext = fromHex(bundle.encryptedPrivateKey);

  const aesKey = await deriveAesKey(combined, salt);
  const privateKeyDer = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: iv.buffer as ArrayBuffer },
    aesKey,
    ciphertext.buffer as ArrayBuffer,
  );

  const privateKey = await crypto.subtle.importKey(
    "pkcs8",
    privateKeyDer,
    { name: "ECDSA", namedCurve: "P-256" },
    false,
    ["sign"],
  );

  return { privateKey, recoveredFaceMessage, recoveredEarMessage };
}

/**
 * Append fresh face and ear helpers derived from a successfully verified
 * dual-modality capture. Both helper sets grow together and are capped
 * at MAX_HELPERS each.
 */
export function appendAdaptiveHelper(
  bundle: EncryptedKeyBundle,
  recoveredFaceMessage: Uint8Array,
  recoveredEarMessage: Uint8Array,
  faceDescriptor: FeatureDescriptor,
  earDescriptor: FeatureDescriptor,
): EncryptedKeyBundle {
  if (bundle.format !== "fuzzy-extractor-rs-v4") {
    return bundle;
  }
  const params = bundle.quantisationParams ?? ENROLLMENT_QUANTISATION_PARAMS;

  const newFaceHelper = buildHelper(faceDescriptor, recoveredFaceMessage, params);
  const newEarHelper = buildHelper(
    earDescriptor,
    recoveredEarMessage,
    EAR_QUANTISATION_PARAMS,
  );

  const faceHelpers = [...(bundle.face_helpers ?? [])];
  const earHelpers = [...(bundle.ear_helpers ?? [])];

  // Skip if this exact helper is already the most recent — avoids
  // bloating the bundle on repeated verifications under identical
  // conditions.
  if (faceHelpers[faceHelpers.length - 1] !== newFaceHelper) {
    faceHelpers.push(newFaceHelper);
    while (faceHelpers.length > MAX_HELPERS) faceHelpers.shift();
  }
  if (earHelpers[earHelpers.length - 1] !== newEarHelper) {
    earHelpers.push(newEarHelper);
    while (earHelpers.length > MAX_HELPERS) earHelpers.shift();
  }

  return {
    ...bundle,
    face_helpers: faceHelpers,
    ear_helpers: earHelpers,
  };
}
