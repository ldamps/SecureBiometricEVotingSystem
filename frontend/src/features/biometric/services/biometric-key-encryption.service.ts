/**
 * Biometric-bound key encryption using a multi-helper fuzzy extractor with
 * Reed-Solomon error correction.
 *
 * Design — multi-helper code-offset fuzzy extractor (Dodis, Reyzin, Smith
 * 2004 extended with per-capture helpers and adaptive update):
 *
 *   Enrollment (N captures under deliberately varied lighting/pose):
 *     1. Pick ONE uniformly random 16-byte message m.
 *     2. Encode m with Reed-Solomon (n=48, k=16) → 48-byte codeword c.
 *     3. For each capture i ∈ [0, N): quantise descriptor → b_i; store
 *        helper_i = c XOR b_i. All helpers encode the same m, so any one
 *        of them that decodes recovers the same AES key.
 *     4. Derive AES-256 key K = PBKDF2(m, salt, 100k iterations).
 *     5. Encrypt the ECDSA signing key under K with AES-GCM.
 *
 *   Verification:
 *     1. Capture a fresh face descriptor, quantise → b'.
 *     2. For each stored helper_i: try noisy_c = helper_i XOR b';
 *        RS-decode. First helper that decodes recovers m → K → private key.
 *     3. AES-GCM tag validates recovery was correct.
 *
 *   Adaptive update (after successful verification):
 *     1. Recompute c = rsEncode(m) (deterministic from m).
 *     2. Build new_helper = c XOR b' (fresh descriptor).
 *     3. Append to helpers array; drop oldest if at capacity. No
 *        re-enrollment required.
 *
 * Why multiple helpers:
 *   A single enrollment snapshot locks in one lighting/pose configuration.
 *   Cross-session drift under different conditions can exceed the per-byte
 *   RS correction budget (≤ 16 of 48 bytes), causing hard failure days
 *   later. Multiple helpers cover a wider variation envelope; adaptive
 *   update continuously folds in new conditions as the user experiences
 *   them, so the system grows more robust with use — not less.
 *
 * Security:
 *   - helpers are information-theoretically hiding under standard
 *     fuzzy-extractor assumptions (each helper is c XOR b_i where b_i has
 *     high min-entropy; c is pseudorandom under m).
 *   - Adding helpers does not reduce entropy of m — they all mask the SAME
 *     codeword, so an attacker with k helpers learns at most k quantised
 *     descriptor regions, not m itself.
 *   - Nothing biometric is stored: helpers, salt, iv, and the AES-GCM
 *     ciphertext are all that is written to the server.
 */

import {
  FeatureDescriptor,
  EncryptedKeyBundle,
  QuantisationParams,
  ENROLLMENT_QUANTISATION_PARAMS,
  MAX_HELPERS,
} from "../models/biometric-feature.model";
import { rsEncode, rsDecode, RS_PARAMS } from "./reed-solomon.service";

const FACE_DESCRIPTOR_LEN = 128;

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
  if (values.length !== FACE_DESCRIPTOR_LEN) {
    throw new Error(`Expected ${FACE_DESCRIPTOR_LEN} values, got ${values.length}.`);
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
  if (descriptor.length !== FACE_DESCRIPTOR_LEN) {
    throw new Error(
      `Expected ${FACE_DESCRIPTOR_LEN}-dim descriptor, got ${descriptor.length}.`,
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
    message.buffer as ArrayBuffer,
    "PBKDF2",
    false,
    ["deriveKey"],
  );
  return crypto.subtle.deriveKey(
    {
      name: "PBKDF2",
      salt: salt.buffer as ArrayBuffer,
      iterations: 100_000,
      hash: "SHA-256",
    },
    keyMaterial,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"],
  );
}

// ----- Public enrollment + verification API -----

/**
 * Generate an ECDSA keypair and encrypt the private key under a biometric-
 * bound AES key. Accepts N enrolment face descriptors captured under
 * different conditions; stores one helper per descriptor, all encoding the
 * same random message. Any future capture that's close to ANY enrolled
 * descriptor decrypts the key.
 */
export async function generateAndEncryptKeyPair(
  faceDescriptors: FeatureDescriptor[],
  _earDescriptor: FeatureDescriptor,
  params: QuantisationParams = ENROLLMENT_QUANTISATION_PARAMS,
): Promise<{ publicKeyPem: string; encryptedBundle: EncryptedKeyBundle }> {
  if (faceDescriptors.length === 0) {
    throw new Error("At least one enrolment face descriptor is required.");
  }

  // 1. One random message shared across all helpers.
  const m = crypto.getRandomValues(new Uint8Array(RS_PARAMS.k));

  // 2. RS-encode once — every helper masks the same codeword.
  const c = rsEncode(m, RS_PARAMS.nsym);

  // 3. Build one helper per enrolment descriptor.
  const helpers: string[] = [];
  for (const descriptor of faceDescriptors) {
    const b = descriptorToBytes(descriptor, params);
    const helper = new Uint8Array(RS_PARAMS.n);
    for (let i = 0; i < RS_PARAMS.n; i++) helper[i] = c[i] ^ b[i];
    helpers.push(toHex(helper.buffer as ArrayBuffer));
  }

  // 4. Derive AES key from the random message.
  const salt = crypto.getRandomValues(new Uint8Array(32));
  const aesKey = await deriveAesKey(m, salt);

  // 5. Generate the ECDSA keypair and encrypt the private key.
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
      format: "fuzzy-extractor-rs-v3",
      helpers,
      salt: toHex(salt.buffer as ArrayBuffer),
      iv: toHex(iv.buffer as ArrayBuffer),
      encryptedPrivateKey: toHex(ciphertext),
      quantisationParams: params,
    },
  };
}

/**
 * Recover the ECDSA private key from a fresh biometric capture. Tries each
 * stored helper (v3) or the single legacy helper (v2) and returns the
 * decrypted key along with the recovered message — the message is needed
 * by `appendAdaptiveHelper` to rotate the bundle post-verification.
 */
export async function decryptPrivateKey(
  faceDescriptor: FeatureDescriptor,
  _earDescriptor: FeatureDescriptor,
  bundle: EncryptedKeyBundle,
): Promise<{ privateKey: CryptoKey; recoveredMessage: Uint8Array }> {
  if (
    (bundle.format !== "fuzzy-extractor-rs-v3" &&
      bundle.format !== "fuzzy-extractor-rs-v2") ||
    !bundle.salt ||
    !bundle.iv ||
    !bundle.encryptedPrivateKey
  ) {
    throw new Error(
      "Legacy enrollment format. Please re-enroll once to migrate to the " +
        "durable multi-helper scheme.",
    );
  }

  // v3 holds an array; v2 a single helper. Normalise to a list to try.
  const helperHexes: string[] = bundle.helpers && bundle.helpers.length > 0
    ? bundle.helpers
    : bundle.helper
      ? [bundle.helper]
      : [];
  if (helperHexes.length === 0) {
    throw new Error("Enrollment bundle has no helpers.");
  }

  const params = bundle.quantisationParams ?? ENROLLMENT_QUANTISATION_PARAMS;
  const bPrime = descriptorToBytes(faceDescriptor, params);

  // Try each helper; first one that RS-decodes wins.
  let recovered: Uint8Array | null = null;
  for (const helperHex of helperHexes) {
    const helper = fromHex(helperHex);
    if (helper.length !== RS_PARAMS.n) continue;
    const noisyC = new Uint8Array(RS_PARAMS.n);
    for (let i = 0; i < RS_PARAMS.n; i++) noisyC[i] = helper[i] ^ bPrime[i];
    const corrected = rsDecode(noisyC, RS_PARAMS.nsym);
    if (corrected !== null) {
      recovered = corrected;
      break;
    }
  }
  if (recovered === null) {
    throw new Error(
      "Biometric drift exceeds error-correction capacity for every " +
        "stored helper (face too different from any enrollment — check " +
        "lighting, angle, and camera).",
    );
  }

  const m = recovered.slice(0, RS_PARAMS.k);
  const salt = fromHex(bundle.salt);
  const iv = fromHex(bundle.iv);
  const ciphertext = fromHex(bundle.encryptedPrivateKey);

  const aesKey = await deriveAesKey(m, salt);
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

  return { privateKey, recoveredMessage: m };
}

/**
 * Append a fresh helper derived from a successfully-verified descriptor.
 *
 * Called after `decryptPrivateKey` succeeds: rebuilds the RS codeword from
 * the recovered message, XORs against the quantised fresh descriptor, and
 * appends the result to the bundle's helpers. The oldest helper is dropped
 * if the bundle has reached `MAX_HELPERS`, keeping size bounded while the
 * helper set tracks current biometric conditions.
 *
 * This is what makes the scheme sustainable: every successful verification
 * folds the latest lighting/pose/aging state into the bundle, so the next
 * verification has an even closer match to pick from.
 */
export function appendAdaptiveHelper(
  bundle: EncryptedKeyBundle,
  recoveredMessage: Uint8Array,
  faceDescriptor: FeatureDescriptor,
): EncryptedKeyBundle {
  const params = bundle.quantisationParams ?? ENROLLMENT_QUANTISATION_PARAMS;
  const bNew = descriptorToBytes(faceDescriptor, params);

  // Rebuild the codeword deterministically from m; XOR with new biometric.
  const c = rsEncode(recoveredMessage, RS_PARAMS.nsym);
  const helper = new Uint8Array(RS_PARAMS.n);
  for (let i = 0; i < RS_PARAMS.n; i++) helper[i] = c[i] ^ bNew[i];
  const newHelperHex = toHex(helper.buffer as ArrayBuffer);

  // Collect existing helpers (normalising v2 → v3 on the fly).
  const existing: string[] = bundle.helpers && bundle.helpers.length > 0
    ? [...bundle.helpers]
    : bundle.helper
      ? [bundle.helper]
      : [];

  // Skip if this exact helper is already the most recent — avoids bloating
  // the bundle on repeated verifications under identical conditions.
  if (existing[existing.length - 1] === newHelperHex) {
    return { ...bundle, format: "fuzzy-extractor-rs-v3", helpers: existing };
  }

  existing.push(newHelperHex);
  while (existing.length > MAX_HELPERS) existing.shift();

  const updated: EncryptedKeyBundle = {
    ...bundle,
    format: "fuzzy-extractor-rs-v3",
    helpers: existing,
  };
  // v3 stores only `helpers`; drop the legacy single-helper field once
  // we've upgraded so the bundle doesn't carry dead weight.
  delete updated.helper;
  return updated;
}
