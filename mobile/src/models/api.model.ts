/**
 * API request/response types matching the backend schemas.
 * Identical to the web frontend's biometric.model.ts.
 */

export interface EnrollDeviceRequest {
  voter_id: string;
  public_key_pem: string;
  device_id: string;
  modalities?: string;
  attestation?: string;
  device_label?: string;
  encrypted_key_bundle?: string;
}

export interface EnrollDeviceResponse {
  id: string;
  voter_id: string;
  device_id: string;
  modalities: string;
  is_active: boolean;
  enrolled_at: string;
}

export interface CreateChallengeRequest {
  voter_id: string;
}

export interface CreateChallengeResponse {
  id: string;
  challenge: string;
  expires_at: string;
}

export interface VerifyBiometricRequest {
  challenge_id: string;
  device_id: string;
  signature: string;
}

export interface VerifyBiometricResponse {
  verified: boolean;
  voter_id?: string;
  message: string;
}

export interface DeviceCredential {
  id: string;
  voter_id: string;
  device_id: string;
  modalities: string;
  device_label?: string;
  is_active: boolean;
  last_used_at?: string;
  created_at: string;
  encrypted_key_bundle?: string;
}
