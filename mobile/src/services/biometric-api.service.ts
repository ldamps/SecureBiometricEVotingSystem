/**
 * Biometric API client — mirrors the web frontend's BiometricApiRepository.
 */

import { ApiClient } from "./api-client.service";
import {
  EnrollDeviceRequest,
  EnrollDeviceResponse,
  CreateChallengeRequest,
  CreateChallengeResponse,
  VerifyBiometricRequest,
  VerifyBiometricResponse,
  DeviceCredential,
} from "../models/api.model";

const ROOT = "/biometric";

export const BiometricApi = {
  enrollDevice: (body: EnrollDeviceRequest) =>
    ApiClient.post<EnrollDeviceResponse>(`${ROOT}/enroll`, body),

  createChallenge: (body: CreateChallengeRequest) =>
    ApiClient.post<CreateChallengeResponse>(`${ROOT}/challenge`, body),

  verifyBiometric: (body: VerifyBiometricRequest) =>
    ApiClient.post<VerifyBiometricResponse>(`${ROOT}/verify`, body),

  listCredentials: (voterId: string) =>
    ApiClient.get<DeviceCredential[]>(`${ROOT}/${voterId}/credentials`),
};
