// Biometric models — match-on-device architecture
// The mobile device handles all biometric capture/matching.
// The voting platform only sees public keys and cryptographic proofs.

// --- Enrollment ---

export interface EnrollDeviceRequest {
    voter_id: string;
    public_key_pem: string;
    device_id: string;
    modalities?: string;
    attestation?: string;
    device_label?: string;
}

export interface EnrollDeviceResponse {
    id: string;
    voter_id: string;
    device_id: string;
    modalities: string;
    is_active: boolean;
    enrolled_at: string;
}

// --- Challenge-response verification ---

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

// --- Device credential listing ---

export interface DeviceCredential {
    id: string;
    voter_id: string;
    device_id: string;
    modalities: string;
    device_label?: string;
    is_active: boolean;
    last_used_at?: string;
    created_at: string;
}

// --- Enrollment status (used by the registration UI) ---

export enum BiometricEnrollmentStatus {
    NOT_STARTED = "NOT_STARTED",
    WAITING_FOR_DEVICE = "WAITING_FOR_DEVICE",
    CAPTURING = "CAPTURING",
    ENROLLING = "ENROLLING",
    ENROLLED = "ENROLLED",
    ERROR = "ERROR",
}

// --- Verification status (used by the voting verification UI) ---

export enum BiometricVerificationStatus {
    IDLE = "IDLE",
    CHALLENGE_ISSUED = "CHALLENGE_ISSUED",
    AWAITING_DEVICE = "AWAITING_DEVICE",
    VERIFYING = "VERIFYING",
    VERIFIED = "VERIFIED",
    FAILED = "FAILED",
}
