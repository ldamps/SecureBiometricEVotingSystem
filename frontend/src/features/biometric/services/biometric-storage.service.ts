/**
 * IndexedDB persistence for biometric enrollment data.
 *
 * Stores:
 *  - Face and ear reference templates (feature vectors)
 *  - AES-GCM encrypted ECDSA private key bundle
 *
 * The raw private key is never stored; only the biometric-encrypted
 * ciphertext is persisted.
 */

import { StoredBiometricData } from "../models/biometric-feature.model";

const DB_NAME = "evoting_biometric_store";
const DB_VERSION = 1;
const STORE_NAME = "biometric_data";

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function storeBiometricData(
  data: StoredBiometricData,
): Promise<void> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).put(data, data.voterId);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function retrieveBiometricData(
  voterId: string,
): Promise<StoredBiometricData | null> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readonly");
    const req = tx.objectStore(STORE_NAME).get(voterId);
    req.onsuccess = () => resolve(req.result ?? null);
    req.onerror = () => reject(req.error);
  });
}

export async function deleteBiometricData(voterId: string): Promise<void> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).delete(voterId);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}
