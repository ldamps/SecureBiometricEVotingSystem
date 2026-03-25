// biometric-api.repository.ts — API client for match-on-device biometric flow

import { ApiClient } from "../../../services/api-client.service";
import {
    EnrollDeviceRequest,
    EnrollDeviceResponse,
    CreateChallengeRequest,
    CreateChallengeResponse,
    VerifyBiometricRequest,
    VerifyBiometricResponse,
    DeviceCredential,
} from "../model/biometric.model";

const ROOT = "/biometric";

export class BiometricApiRepository {
    // --- Enrollment ---

    async enrollDevice(body: EnrollDeviceRequest): Promise<EnrollDeviceResponse> {
        return ApiClient.post<EnrollDeviceResponse>(`${ROOT}/enroll`, body);
    }

    // --- Challenge-response verification ---

    async createChallenge(body: CreateChallengeRequest): Promise<CreateChallengeResponse> {
        return ApiClient.post<CreateChallengeResponse>(`${ROOT}/challenge`, body);
    }

    async verifyBiometric(body: VerifyBiometricRequest): Promise<VerifyBiometricResponse> {
        return ApiClient.post<VerifyBiometricResponse>(`${ROOT}/verify`, body);
    }

    // --- Credential management ---

    async listCredentials(voterId: string): Promise<DeviceCredential[]> {
        return ApiClient.get<DeviceCredential[]>(`${ROOT}/${voterId}/credentials`);
    }

    async revokeCredential(credentialId: string): Promise<void> {
        await ApiClient.delete(`${ROOT}/credentials/${credentialId}`);
    }
}
