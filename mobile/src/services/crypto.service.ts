/**
 * Cryptographic operations using react-native-quick-crypto.
 *
 * Provides the same WebCrypto-compatible API surface used by the
 * biometric key encryption service on the web frontend.
 */

import QuickCrypto from "react-native-quick-crypto";

// react-native-quick-crypto exposes a WebCrypto-compatible API.
// Use it as a drop-in replacement for window.crypto.subtle.
const subtle = QuickCrypto.subtle ?? (QuickCrypto as any).webcrypto?.subtle;

export async function generateECDSAKeyPair(): Promise<CryptoKeyPair> {
  return subtle.generateKey(
    { name: "ECDSA", namedCurve: "P-256" },
    true,
    ["sign", "verify"],
  );
}

export async function exportPublicKeyPem(publicKey: CryptoKey): Promise<string> {
  const spki = await subtle.exportKey("spki", publicKey);
  const base64 = arrayBufferToBase64(spki);
  return (
    "-----BEGIN PUBLIC KEY-----\n" +
    base64.match(/.{1,64}/g)!.join("\n") +
    "\n-----END PUBLIC KEY-----"
  );
}

export async function exportPrivateKeyDer(privateKey: CryptoKey): Promise<ArrayBuffer> {
  return subtle.exportKey("pkcs8", privateKey);
}

export async function importPrivateKey(pkcs8: ArrayBuffer): Promise<CryptoKey> {
  return subtle.importKey(
    "pkcs8",
    pkcs8,
    { name: "ECDSA", namedCurve: "P-256" },
    false,
    ["sign"],
  );
}

export async function signData(
  privateKey: CryptoKey,
  data: ArrayBuffer,
): Promise<ArrayBuffer> {
  return subtle.sign({ name: "ECDSA", hash: "SHA-256" }, privateKey, data);
}

export async function deriveAesKey(
  keyMaterial: ArrayBuffer,
  salt: ArrayBuffer,
): Promise<CryptoKey> {
  const material = await subtle.importKey("raw", keyMaterial, "PBKDF2", false, [
    "deriveKey",
  ]);
  return subtle.deriveKey(
    { name: "PBKDF2", salt, iterations: 100_000, hash: "SHA-256" },
    material,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"],
  );
}

export async function encryptAesGcm(
  key: CryptoKey,
  iv: ArrayBuffer,
  plaintext: ArrayBuffer,
): Promise<ArrayBuffer> {
  return subtle.encrypt({ name: "AES-GCM", iv }, key, plaintext);
}

export async function decryptAesGcm(
  key: CryptoKey,
  iv: ArrayBuffer,
  ciphertext: ArrayBuffer,
): Promise<ArrayBuffer> {
  return subtle.decrypt({ name: "AES-GCM", iv }, key, ciphertext);
}

export function getRandomBytes(length: number): Uint8Array {
  return QuickCrypto.getRandomValues(new Uint8Array(length));
}

export function randomUUID(): string {
  return QuickCrypto.randomUUID?.() ?? generateUUIDv4();
}

// Helpers

export function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return globalThis.btoa?.(binary) ?? base64Encode(bytes);
}

export function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binary = globalThis.atob?.(base64) ?? base64Decode(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer as ArrayBuffer;
}

export function toHex(buf: ArrayBuffer): string {
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export function fromHex(hex: string): ArrayBuffer {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < bytes.length; i++) {
    bytes[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  }
  return bytes.buffer as ArrayBuffer;
}

function generateUUIDv4(): string {
  const bytes = QuickCrypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = toHex(bytes.buffer as ArrayBuffer);
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

// Base64 fallback for environments without btoa/atob
const B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

function base64Encode(bytes: Uint8Array): string {
  let result = "";
  for (let i = 0; i < bytes.length; i += 3) {
    const b0 = bytes[i], b1 = bytes[i + 1] ?? 0, b2 = bytes[i + 2] ?? 0;
    result += B64[(b0 >> 2)];
    result += B64[((b0 & 3) << 4) | (b1 >> 4)];
    result += i + 1 < bytes.length ? B64[((b1 & 15) << 2) | (b2 >> 6)] : "=";
    result += i + 2 < bytes.length ? B64[(b2 & 63)] : "=";
  }
  return result;
}

function base64Decode(str: string): string {
  let result = "";
  const cleaned = str.replace(/[^A-Za-z0-9+/]/g, "");
  for (let i = 0; i < cleaned.length; i += 4) {
    const b0 = B64.indexOf(cleaned[i]);
    const b1 = B64.indexOf(cleaned[i + 1]);
    const b2 = B64.indexOf(cleaned[i + 2]);
    const b3 = B64.indexOf(cleaned[i + 3]);
    result += String.fromCharCode((b0 << 2) | (b1 >> 4));
    if (b2 >= 0) result += String.fromCharCode(((b1 & 15) << 4) | (b2 >> 2));
    if (b3 >= 0) result += String.fromCharCode(((b2 & 3) << 6) | b3);
  }
  return result;
}
