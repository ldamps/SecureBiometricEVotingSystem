/**
 * Biometric-bound key encryption with cross-device tolerance.
 *
 * During enrollment the ECDSA private key is encrypted multiple times,
 * each with a slightly different quantisation offset applied to the
 * face feature vector.  This produces 13 encrypted copies that cover
 * the natural variation between cameras, lighting, and angles.
 *
 * During verification the system tries to decrypt each copy with the
 * fresh biometric.  If ANY copy's AES-GCM tag validates, the private
 * key is recovered — proving the same person is present.
 *
 * KEY DESIGN DECISION — face-only key derivation:
 * Only the face descriptor (128-d, from the face-api.js deep learning
 * model) is used for AES key derivation.  The ear descriptor is
 * intentionally excluded because the hand-crafted pixel-level ear
 * features (spatial block means, gradient histograms, LBP textures)
 * are too sensitive to head position, lighting, and camera angle to
 * survive quantisation reliably across sessions.  The ear biometric
 * is still captured and verified via cosine-similarity advisory
 * matching (see biometric-matching.service.ts).
 *
 * With 128 face dimensions × 4 bins the key space is 2^256, which
 * exactly matches the 256-bit AES key — security is not compromised.
 *
 * What is stored: encrypted key copies (salt + IV + ciphertext each).
 * What is NOT stored: biometric templates, feature vectors, images.
 */

import {
  FeatureDescriptor,
  EncryptedKeyBundle,
  EncryptedKeyCopy,
  QuantisationParams,
  DEFAULT_QUANTISATION_PARAMS,
} from "../models/biometric-feature.model";

function toHex(buf: ArrayBuffer): string {
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function fromHex(hex: string): ArrayBuffer {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < bytes.length; i++) {
    bytes[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  }
  return bytes.buffer as ArrayBuffer;
}

/**
 * Quantise each dimension into a bin, with an optional offset shift
 * applied to the bin boundaries.
 */
function quantiseFeatures(
  descriptor: FeatureDescriptor,
  params: QuantisationParams,
  offset: number = 0,
): Uint8Array {
  const { numBins, rangeMin, rangeMax } = params;
  const binWidth = (rangeMax - rangeMin) / numBins;
  const quantised = new Uint8Array(descriptor.length);
  for (let i = 0; i < descriptor.length; i++) {
    const shifted = descriptor[i] - offset;
    const clamped = Math.max(rangeMin, Math.min(rangeMax - 1e-9, shifted));
    quantised[i] = Math.floor((clamped - rangeMin) / binWidth);
  }
  return quantised;
}

async function deriveAesKey(
  quantised: Uint8Array,
  salt: ArrayBuffer,
): Promise<CryptoKey> {
  const keyMaterial = await crypto.subtle.importKey(
    "raw",
    quantised.buffer as ArrayBuffer,
    "PBKDF2",
    false,
    ["deriveKey"],
  );
  return crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations: 100_000, hash: "SHA-256" },
    keyMaterial,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"],
  );
}

/**
 * Generate quantisation offsets that cover cross-session biometric
 * variation.  Each offset shifts all bin boundaries by a small amount,
 * so dimensions near a boundary get a chance to land in the correct bin
 * even when lighting, angle, or camera conditions differ slightly.
 *
 * With 4 bins across [-1, 1] the bin width is 0.5.  Using 13 offsets
 * at ±0.02 steps up to ±0.12 means the net offset between any
 * (enrollment copy, verification offset) pair can reach ±0.24 —
 * covering ~48% of the bin width.  This handles the rare boundary
 * cases while preserving security (the attacker must still guess
 * the correct quantised bin for every dimension).
 */
function generateOffsets(): number[] {
  const offsets: number[] = [0]; // always include zero-offset (exact match)
  for (const delta of [0.02, 0.04, 0.06, 0.08, 0.10, 0.12]) {
    offsets.push(delta);
    offsets.push(-delta);
  }
  return offsets; // 13 offsets total
}

/**
 * Encrypt the private key once with the given quantisation offset.
 */
async function encryptOneCopy(
  combined: FeatureDescriptor,
  params: QuantisationParams,
  offset: number,
  privateKeyDer: ArrayBuffer,
): Promise<EncryptedKeyCopy> {
  const quantised = quantiseFeatures(combined, params, offset);
  const salt = crypto.getRandomValues(new Uint8Array(32));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const aesKey = await deriveAesKey(quantised, salt.buffer as ArrayBuffer);
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: iv.buffer as ArrayBuffer },
    aesKey,
    privateKeyDer,
  );
  return {
    salt: toHex(salt.buffer as ArrayBuffer),
    iv: toHex(iv.buffer as ArrayBuffer),
    encryptedPrivateKey: toHex(ciphertext),
  };
}

/**
 * Generate an ECDSA P-256 keypair and encrypt the private key multiple
 * times with different quantisation offsets.
 */
export async function generateAndEncryptKeyPair(
  faceDescriptor: FeatureDescriptor,
  _earDescriptor: FeatureDescriptor,
  params: QuantisationParams = DEFAULT_QUANTISATION_PARAMS,
): Promise<{ publicKeyPem: string; encryptedBundle: EncryptedKeyBundle }> {
  // Use only the face descriptor for key derivation — see module doc
  // for rationale.  The ear descriptor is verified separately via
  // cosine-similarity advisory matching.
  const combined = new Float32Array(faceDescriptor.length);
  combined.set(faceDescriptor);

  // Generate ECDSA keypair (extractable).
  const keyPair = await crypto.subtle.generateKey(
    { name: "ECDSA", namedCurve: "P-256" },
    true,
    ["sign", "verify"],
  );

  // Export private key.
  const privateKeyDer = await crypto.subtle.exportKey("pkcs8", keyPair.privateKey);

  // Encrypt with each offset.
  const offsets = generateOffsets();
  const copies: EncryptedKeyCopy[] = [];
  for (const offset of offsets) {
    copies.push(await encryptOneCopy(combined, params, offset, privateKeyDer));
  }

  // Export public key as PEM.
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
      copies,
      quantisationParams: params,
    },
  };
}

/**
 * Try to decrypt the ECDSA private key using a fresh biometric capture.
 *
 * Iterates through all encrypted copies, attempting decryption with the
 * zero-offset quantisation first (most likely match), then each offset
 * variant.  Returns as soon as any copy's AES-GCM tag validates.
 *
 * Throws if no copy can be decrypted (biometric mismatch).
 */
export async function decryptPrivateKey(
  faceDescriptor: FeatureDescriptor,
  _earDescriptor: FeatureDescriptor,
  bundle: EncryptedKeyBundle,
): Promise<CryptoKey> {
  const quantisationParams = bundle.quantisationParams ?? DEFAULT_QUANTISATION_PARAMS;

  // Use only the face descriptor (matches enrollment).
  const combined = new Float32Array(faceDescriptor.length);
  combined.set(faceDescriptor);

  // Build the list of copies to try.
  let copies: EncryptedKeyCopy[];
  if (bundle.copies && bundle.copies.length > 0) {
    copies = bundle.copies;
  } else if (bundle.salt && bundle.iv && bundle.encryptedPrivateKey) {
    // Backward compatibility with single-copy bundles.
    copies = [{ salt: bundle.salt, iv: bundle.iv, encryptedPrivateKey: bundle.encryptedPrivateKey }];
  } else {
    throw new Error("Invalid encrypted key bundle.");
  }

  // Generate the same offsets used during enrollment.
  const offsets = generateOffsets();

  // Try every (copy, offset) combination.
  // The copy at index i was encrypted with offset[i], but due to
  // cross-device drift, a DIFFERENT offset applied to the fresh
  // biometric might match a copy encrypted with offset 0 and vice versa.
  // So we try all offsets against all copies for maximum tolerance.
  for (const copy of copies) {
    for (const offset of offsets) {
      try {
        const quantised = quantiseFeatures(combined, quantisationParams, offset);
        const aesKey = await deriveAesKey(quantised, fromHex(copy.salt));
        const privateKeyDer = await crypto.subtle.decrypt(
          { name: "AES-GCM", iv: fromHex(copy.iv) },
          aesKey,
          fromHex(copy.encryptedPrivateKey),
        );
        // AES-GCM tag validated — this is the correct key.
        return crypto.subtle.importKey(
          "pkcs8",
          privateKeyDer,
          { name: "ECDSA", namedCurve: "P-256" },
          false,
          ["sign"],
        );
      } catch {
        // Wrong key — try next combination.
      }
    }
  }

  throw new Error("Biometric mismatch — none of the encrypted key copies could be decrypted.");
}
