/**
 * Biometric-bound key encryption — ported from the web frontend.
 *
 * Identical algorithm: quantise face features, derive AES key via
 * PBKDF2, encrypt/decrypt the ECDSA private key with AES-GCM.
 * The only change is using react-native-quick-crypto instead of
 * window.crypto.subtle.
 *
 * KEY DESIGN DECISION — face-only key derivation:
 * Only the face descriptor is used for AES key derivation.  The ear
 * descriptor is excluded because hand-crafted pixel-level ear features
 * are too sensitive to position/lighting to survive quantisation across
 * sessions.  The ear is still verified via cosine-similarity matching.
 */

import {
  FeatureDescriptor,
  EncryptedKeyBundle,
  EncryptedKeyCopy,
  QuantisationParams,
  DEFAULT_QUANTISATION_PARAMS,
} from "../models/biometric-feature.model";

import {
  generateECDSAKeyPair,
  exportPublicKeyPem,
  exportPrivateKeyDer,
  importPrivateKey,
  deriveAesKey,
  encryptAesGcm,
  decryptAesGcm,
  getRandomBytes,
  toHex,
  fromHex,
} from "./crypto.service";

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

function generateOffsets(): number[] {
  const offsets: number[] = [0]; // always include zero-offset (exact match)
  for (const delta of [0.02, 0.04, 0.06, 0.08, 0.10, 0.12]) {
    offsets.push(delta);
    offsets.push(-delta);
  }
  return offsets; // 13 offsets total
}

async function encryptOneCopy(
  combined: FeatureDescriptor,
  params: QuantisationParams,
  offset: number,
  privateKeyDer: ArrayBuffer,
): Promise<EncryptedKeyCopy> {
  const quantised = quantiseFeatures(combined, params, offset);
  const salt = getRandomBytes(32);
  const iv = getRandomBytes(12);
  const aesKey = await deriveAesKey(
    quantised.buffer as ArrayBuffer,
    salt.buffer as ArrayBuffer,
  );
  const ciphertext = await encryptAesGcm(
    aesKey,
    iv.buffer as ArrayBuffer,
    privateKeyDer,
  );
  return {
    salt: toHex(salt.buffer as ArrayBuffer),
    iv: toHex(iv.buffer as ArrayBuffer),
    encryptedPrivateKey: toHex(ciphertext),
  };
}

/** Generate ECDSA keypair and encrypt private key with biometric features. */
export async function generateAndEncryptKeyPair(
  faceDescriptor: FeatureDescriptor,
  _earDescriptor: FeatureDescriptor,
  params: QuantisationParams = DEFAULT_QUANTISATION_PARAMS,
): Promise<{ publicKeyPem: string; encryptedBundle: EncryptedKeyBundle }> {
  // Use only face descriptor for key derivation — see module doc.
  const combined = new Float32Array(faceDescriptor.length);
  combined.set(faceDescriptor);

  const keyPair = await generateECDSAKeyPair();
  const privateKeyDer = await exportPrivateKeyDer(keyPair.privateKey);
  const publicKeyPem = await exportPublicKeyPem(keyPair.publicKey);

  const offsets = generateOffsets();
  const copies: EncryptedKeyCopy[] = [];
  for (const offset of offsets) {
    copies.push(await encryptOneCopy(combined, params, offset, privateKeyDer));
  }

  return {
    publicKeyPem,
    encryptedBundle: { copies, quantisationParams: params },
  };
}

/** Decrypt the ECDSA private key using fresh biometric features. */
export async function decryptPrivateKey(
  faceDescriptor: FeatureDescriptor,
  _earDescriptor: FeatureDescriptor,
  bundle: EncryptedKeyBundle,
): Promise<CryptoKey> {
  const { quantisationParams } = bundle;

  // Use only face descriptor (matches enrollment).
  const combined = new Float32Array(faceDescriptor.length);
  combined.set(faceDescriptor);

  let copies: EncryptedKeyCopy[];
  if (bundle.copies && bundle.copies.length > 0) {
    copies = bundle.copies;
  } else if (bundle.salt && bundle.iv && bundle.encryptedPrivateKey) {
    copies = [{ salt: bundle.salt, iv: bundle.iv, encryptedPrivateKey: bundle.encryptedPrivateKey }];
  } else {
    throw new Error("Invalid encrypted key bundle.");
  }

  const offsets = generateOffsets();

  for (const copy of copies) {
    for (const offset of offsets) {
      try {
        const quantised = quantiseFeatures(combined, quantisationParams, offset);
        const aesKey = await deriveAesKey(
          quantised.buffer as ArrayBuffer,
          fromHex(copy.salt),
        );
        const privateKeyDer = await decryptAesGcm(
          aesKey,
          fromHex(copy.iv),
          fromHex(copy.encryptedPrivateKey),
        );
        return importPrivateKey(privateKeyDer);
      } catch {
        // Wrong key — try next combination.
      }
    }
  }

  throw new Error("Biometric mismatch — none of the encrypted key copies could be decrypted.");
}

/** Sign a hex-encoded challenge with an ECDSA private key. */
export async function signChallenge(
  privateKey: CryptoKey,
  challengeHex: string,
): Promise<string> {
  const { signData, arrayBufferToBase64 } = await import("./crypto.service");
  const challengeBytes = new Uint8Array(
    challengeHex.match(/.{1,2}/g)!.map((byte) => parseInt(byte, 16)),
  );
  const signature = await signData(privateKey, challengeBytes.buffer as ArrayBuffer);
  return arrayBufferToBase64(signature);
}
