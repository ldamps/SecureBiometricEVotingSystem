/**
 * Secure storage for biometric enrollment data.
 *
 * Uses expo-secure-store which persists to:
 *   - iOS: Keychain (hardware-backed, survives app reinstall)
 *   - Android: EncryptedSharedPreferences (Android Keystore-backed)
 *
 * This is the critical advantage over the web frontend's IndexedDB:
 * data survives browser cache clearing and is hardware-protected.
 *
 * expo-secure-store has a 2KB-per-key limit, so the encrypted key
 * bundle (which can exceed 2KB) is chunked across multiple keys.
 */

import * as SecureStore from "expo-secure-store";
import { StoredBiometricData } from "../models/biometric-feature.model";

const DEVICE_ID_KEY = "evoting_device_id";
const BIOMETRIC_PREFIX = "evoting_bio_";
const CHUNK_SIZE = 1800; // leave headroom under 2KB limit

/** Get or create a persistent device ID. */
export async function getDeviceId(): Promise<string> {
  let id = await SecureStore.getItemAsync(DEVICE_ID_KEY);
  if (!id) {
    id = generateUUID();
    await SecureStore.setItemAsync(DEVICE_ID_KEY, id);
  }
  return id;
}

/** Store biometric enrollment data for a voter. */
export async function storeBiometricData(
  data: StoredBiometricData,
): Promise<void> {
  const json = JSON.stringify(data);
  const chunks = chunkString(json, CHUNK_SIZE);

  // Store chunk count
  await SecureStore.setItemAsync(
    `${BIOMETRIC_PREFIX}${data.voterId}_count`,
    String(chunks.length),
  );

  // Store each chunk
  for (let i = 0; i < chunks.length; i++) {
    await SecureStore.setItemAsync(
      `${BIOMETRIC_PREFIX}${data.voterId}_${i}`,
      chunks[i],
    );
  }
}

/** Retrieve biometric enrollment data for a voter. */
export async function retrieveBiometricData(
  voterId: string,
): Promise<StoredBiometricData | null> {
  const countStr = await SecureStore.getItemAsync(
    `${BIOMETRIC_PREFIX}${voterId}_count`,
  );
  if (!countStr) return null;

  const count = parseInt(countStr, 10);
  if (isNaN(count) || count <= 0) return null;

  let json = "";
  for (let i = 0; i < count; i++) {
    const chunk = await SecureStore.getItemAsync(
      `${BIOMETRIC_PREFIX}${voterId}_${i}`,
    );
    if (!chunk) return null; // corrupted — missing chunk
    json += chunk;
  }

  try {
    return JSON.parse(json) as StoredBiometricData;
  } catch {
    return null;
  }
}

/** Delete biometric enrollment data for a voter. */
export async function deleteBiometricData(voterId: string): Promise<void> {
  const countStr = await SecureStore.getItemAsync(
    `${BIOMETRIC_PREFIX}${voterId}_count`,
  );
  if (countStr) {
    const count = parseInt(countStr, 10);
    for (let i = 0; i < count; i++) {
      await SecureStore.deleteItemAsync(`${BIOMETRIC_PREFIX}${voterId}_${i}`);
    }
  }
  await SecureStore.deleteItemAsync(`${BIOMETRIC_PREFIX}${voterId}_count`);
}

function chunkString(str: string, size: number): string[] {
  const chunks: string[] = [];
  for (let i = 0; i < str.length; i += size) {
    chunks.push(str.slice(i, i + size));
  }
  return chunks;
}

function generateUUID(): string {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}
