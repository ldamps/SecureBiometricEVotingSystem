/**
 * Biometric-bound key encryption using quantised binning + AES-GCM.
 *
 * Enrollment:
 *   1. Concatenate face (128-d) and ear (128-d) descriptors -> 256-d vector
 *   2. Quantise each dimension into discrete bins
 *   3. Derive an AES-256-GCM key via PBKDF2(quantised_bins, salt)
 *   4. Encrypt the exportable ECDSA private key with that AES key
 *   5. Store { salt, iv, ciphertext, quantisation params } in IndexedDB
 *
 * Verification:
 *   1. Re-capture face + ear, extract descriptors
 *   2. Quantise with the same parameters
 *   3. Re-derive the AES key
 *   4. Attempt AES-GCM decryption — the GCM authentication tag ensures
 *      that only a matching biometric produces the correct key
 *
 * Security property: even with full device access, the ECDSA private key
 * cannot be recovered without a face + ear that quantises to the same bins.
 */

import {
  FeatureDescriptor,
  EncryptedKeyBundle,
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
 * Map each feature dimension to a discrete bin index.
 *
 * Values are clamped to [rangeMin, rangeMax] then divided into
 * `numBins` equal-width bins.  Using a small number of wide bins
 * (default 4) absorbs the natural variation between biometric samples
 * of the same person.
 */
function quantiseFeatures(
  descriptor: FeatureDescriptor,
  params: QuantisationParams,
): Uint8Array {
  const { numBins, rangeMin, rangeMax } = params;
  const binWidth = (rangeMax - rangeMin) / numBins;
  const quantised = new Uint8Array(descriptor.length);
  for (let i = 0; i < descriptor.length; i++) {
    const clamped = Math.max(rangeMin, Math.min(rangeMax - 1e-9, descriptor[i]));
    quantised[i] = Math.floor((clamped - rangeMin) / binWidth);
  }
  return quantised;
}

/**
 * Derive a 256-bit AES-GCM key from quantised biometric bins via PBKDF2.
 */
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
 * Generate an ECDSA P-256 keypair, encrypt the private key with a
 * biometric-derived AES key, and return the public key PEM +
 * encrypted bundle for storage.
 */
export async function generateAndEncryptKeyPair(
  faceDescriptor: FeatureDescriptor,
  earDescriptor: FeatureDescriptor,
  params: QuantisationParams = DEFAULT_QUANTISATION_PARAMS,
): Promise<{ publicKeyPem: string; encryptedBundle: EncryptedKeyBundle }> {
  // 1. Concatenate face + ear into a single 256-d vector.
  const combined = new Float32Array(faceDescriptor.length + earDescriptor.length);
  combined.set(faceDescriptor);
  combined.set(earDescriptor, faceDescriptor.length);

  // 2. Quantise.
  const quantised = quantiseFeatures(combined, params);

  // 3. Generate random salt and IV.
  const salt = crypto.getRandomValues(new Uint8Array(32));
  const iv = crypto.getRandomValues(new Uint8Array(12));

  // 4. Derive AES key from biometric bins.
  const aesKey = await deriveAesKey(quantised, salt.buffer as ArrayBuffer);

  // 5. Generate ECDSA keypair (extractable so we can export the private key).
  const keyPair = await crypto.subtle.generateKey(
    { name: "ECDSA", namedCurve: "P-256" },
    true,
    ["sign", "verify"],
  );

  // 6. Export private key as PKCS8 DER.
  const privateKeyDer = await crypto.subtle.exportKey("pkcs8", keyPair.privateKey);

  // 7. Encrypt private key with AES-GCM (includes authentication tag).
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: iv.buffer as ArrayBuffer },
    aesKey,
    privateKeyDer,
  );

  // 8. Export public key as PEM.
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
      salt: toHex(salt.buffer as ArrayBuffer),
      iv: toHex(iv.buffer as ArrayBuffer),
      encryptedPrivateKey: toHex(ciphertext),
      quantisationParams: params,
    },
  };
}

/**
 * Re-derive the AES key from a fresh biometric capture and decrypt
 * the ECDSA private key.
 *
 * Throws if the biometric features do not quantise to the same bins
 * (the AES-GCM authentication tag will fail).
 */
export async function decryptPrivateKey(
  faceDescriptor: FeatureDescriptor,
  earDescriptor: FeatureDescriptor,
  bundle: EncryptedKeyBundle,
): Promise<CryptoKey> {
  const { salt, iv, encryptedPrivateKey, quantisationParams } = bundle;

  // 1. Concatenate + quantise the fresh descriptors.
  const combined = new Float32Array(faceDescriptor.length + earDescriptor.length);
  combined.set(faceDescriptor);
  combined.set(earDescriptor, faceDescriptor.length);
  const quantised = quantiseFeatures(combined, quantisationParams);

  // 2. Re-derive the AES key.
  const saltBuf = fromHex(salt);
  const aesKey = await deriveAesKey(quantised, saltBuf);

  // 3. Decrypt — will throw DOMException if the key is wrong.
  const privateKeyDer = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: fromHex(iv) },
    aesKey,
    fromHex(encryptedPrivateKey),
  );

  // 4. Import as a non-extractable ECDSA signing key.
  return crypto.subtle.importKey(
    "pkcs8",
    privateKeyDer,
    { name: "ECDSA", namedCurve: "P-256" },
    false,
    ["sign"],
  );
}
