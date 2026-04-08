/**
 * Verification screen — the security-critical path.
 *
 * Three mandatory layers that MUST ALL pass:
 *   L1: Device ID check — this must be the enrolled device
 *   L2: Template matching gate — face AND ear ≥ 0.99 cosine similarity
 *   L3: Biometric key decryption — features must derive the correct AES key
 *
 * If your brother (or anyone who is not you) tries to verify, they will
 * fail at Layer 2 with a clear error showing their similarity scores.
 * Even if L2 were somehow bypassed, L3 would reject them because their
 * features produce a different AES key that cannot decrypt the private key.
 *
 * Mirrors the web frontend's mobileVerifyPage.tsx.
 */

import React, { useState, useCallback, useEffect } from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { Camera } from "react-native-vision-camera";

import StatusCard from "../src/components/StatusCard";
import CaptureOverlay from "../src/components/CaptureOverlay";
import { useCamera } from "../src/hooks/useCamera";
import { useBiometricCapture, CaptureResult } from "../src/hooks/useBiometricCapture";
import { matchBoth } from "../src/services/biometric-matching.service";
import { decryptPrivateKey, signChallenge } from "../src/services/biometric-key-encryption.service";
import { retrieveBiometricData, getDeviceId } from "../src/services/secure-storage.service";
import { BiometricApi } from "../src/services/biometric-api.service";
import { loadFaceModel } from "../src/services/face-recognition.service";
import { loadEarModel } from "../src/services/ear-recognition.service";
import { FeatureDescriptor, EncryptedKeyBundle } from "../src/models/biometric-feature.model";

type VerifyState =
  | "ready"
  | "loading"
  | "capturing"
  | "verifying"
  | "submitting"
  | "success"
  | "error"
  | "no_enrollment"
  | "wrong_device"
  | "biometric_mismatch";

export default function VerifyScreen() {
  const { voter_id, challenge_id } = useLocalSearchParams<{
    voter_id: string;
    challenge_id: string;
  }>();
  const router = useRouter();
  const camera = useCamera();
  const capture = useBiometricCapture("verify");

  const [state, setState] = useState<VerifyState>("ready");
  const [error, setError] = useState<string | null>(null);
  const [encryptedBundle, setEncryptedBundle] = useState<EncryptedKeyBundle | null>(null);
  const [enrolledDeviceId, setEnrolledDeviceId] = useState<string>("");
  const [enrolledFace, setEnrolledFace] = useState<FeatureDescriptor | null>(null);
  const [enrolledEar, setEnrolledEar] = useState<FeatureDescriptor | null>(null);

  useEffect(() => {
    loadFaceModel();
    loadEarModel();
  }, []);

  const handleStartVerify = useCallback(async () => {
    if (!voter_id) return;
    setError(null);
    setState("loading");

    try {
      // 1. Fetch credential from server
      const credentials = await BiometricApi.listCredentials(voter_id);
      const active = credentials.find((c) => c.is_active && c.encrypted_key_bundle);

      if (!active || !active.encrypted_key_bundle) {
        setState("no_enrollment");
        setError("No biometric enrollment found. Please complete enrollment first.");
        return;
      }

      // 2. LAYER 1: Enforce same-device
      const localDeviceId = await getDeviceId();
      if (localDeviceId !== active.device_id) {
        setState("wrong_device");
        setError(
          "This is not the device you enrolled with. " +
          "Biometric verification must be performed on the same phone " +
          "used during enrollment to protect your identity.",
        );
        return;
      }

      // 3. Load enrolled templates from secure storage (Keychain/Keystore)
      const stored = await retrieveBiometricData(voter_id);
      if (!stored || !stored.faceTemplate || !stored.earTemplate) {
        setState("no_enrollment");
        setError(
          "Your enrolled biometric templates were not found on this device. " +
          "Please re-enrol your biometrics from the registration page.",
        );
        return;
      }

      setEncryptedBundle(JSON.parse(active.encrypted_key_bundle));
      setEnrolledDeviceId(active.device_id);
      setEnrolledFace(new Float32Array(stored.faceTemplate));
      setEnrolledEar(new Float32Array(stored.earTemplate));
      setState("capturing");
    } catch (err: any) {
      setError(err.message || "Failed to fetch enrollment data.");
      setState("error");
    }
  }, [voter_id]);

  const handleCaptureComplete = useCallback(
    async (result: CaptureResult) => {
      if (!encryptedBundle || !voter_id) return;

      try {
        setState("verifying");

        // LAYER 2: MANDATORY TEMPLATE MATCHING GATE
        // Both face AND ear must independently reach 99% cosine similarity.
        // This is the primary defence against impostors.
        // If your brother tries this, his face will score ~60-80% and be rejected.
        if (!enrolledFace || !enrolledEar) {
          setState("error");
          setError("Enrolled biometric templates are missing. Please re-enrol.");
          return;
        }

        const match = matchBoth(
          result.faceDescriptor, enrolledFace,
          result.earDescriptor, enrolledEar,
        );

        if (!match.overallPassed) {
          setState("biometric_mismatch");
          setError(
            `Biometric verification failed — you do not match the enrolled voter.\n\n` +
            `Face similarity: ${(match.face.similarity * 100).toFixed(1)}% ` +
            `(${match.face.passed ? "PASS" : "FAIL"})\n` +
            `Ear similarity: ${(match.ear.similarity * 100).toFixed(1)}% ` +
            `(${match.ear.passed ? "PASS" : "FAIL"})\n\n` +
            `Both must be at least 99%.`,
          );
          return;
        }

        // LAYER 3: BIOMETRIC KEY DECRYPTION
        // Even after passing the template gate, the features must also
        // produce the exact AES key that was used during enrollment.
        let privateKey: CryptoKey;
        try {
          privateKey = await decryptPrivateKey(
            result.faceDescriptor,
            result.earDescriptor,
            encryptedBundle,
          );
        } catch {
          setState("biometric_mismatch");
          setError(
            "Biometric key decryption failed. Your features did not produce " +
            "the correct decryption key. Please try again with good lighting.",
          );
          return;
        }

        // Sign the challenge and submit
        setState("submitting");
        const challenge = await BiometricApi.createChallenge({ voter_id });
        const signature = await signChallenge(privateKey, challenge.challenge);

        const verifyResult = await BiometricApi.verifyBiometric({
          challenge_id: challenge.id,
          device_id: enrolledDeviceId,
          signature,
        });

        if (verifyResult.verified) {
          setState("success");
        } else {
          setError(verifyResult.message || "Server rejected the signature.");
          setState("error");
        }
      } catch (err: any) {
        setError(err.message || "Verification failed. Please try again.");
        setState("error");
      }
    },
    [encryptedBundle, voter_id, enrolledDeviceId, enrolledFace, enrolledEar],
  );

  // When capture hook produces a result, process it
  useEffect(() => {
    if (capture.result) {
      handleCaptureComplete(capture.result);
    }
  }, [capture.result, handleCaptureComplete]);

  const messages: Record<VerifyState, { title: string; message: string }> = {
    ready: {
      title: "Biometric Verification",
      message:
        "Verify your identity using your face and ear biometrics. " +
        "You must use the same device you enrolled with. " +
        "Your biometric data never leaves this device.",
    },
    loading: { title: "Loading", message: "Fetching your enrollment data..." },
    capturing: { title: "Capturing", message: "" },
    verifying: { title: "Verifying", message: "Checking your biometrics against your enrolled identity..." },
    submitting: { title: "Submitting", message: "Sending cryptographic proof to the server..." },
    success: {
      title: "Identity Verified",
      message:
        "Your identity has been confirmed. You can now close this screen " +
        "and return to the voting website. It will update automatically.",
    },
    error: { title: "Error", message: "Verification encountered a problem." },
    no_enrollment: { title: "Not Enrolled", message: "No biometric enrollment found for your account." },
    wrong_device: {
      title: "Wrong Device",
      message: "This is not the device you enrolled with. Please use your enrolled phone.",
    },
    biometric_mismatch: {
      title: "Identity Not Confirmed",
      message: "Your biometrics do not match the enrolled voter.",
    },
  };

  const info = messages[state];

  return (
    <View style={styles.container}>
      {state !== "capturing" && (
        <View style={styles.content}>
          <StatusCard
            title={info.title}
            message={info.message}
            error={error}
            variant={
              state === "success" ? "success" :
              state === "biometric_mismatch" || state === "wrong_device" || state === "error" ? "error" :
              "default"
            }
          />

          <View style={styles.buttonRow}>
            {state === "ready" && (
              <TouchableOpacity style={styles.button} onPress={handleStartVerify}>
                <Text style={styles.buttonText}>Verify Identity</Text>
              </TouchableOpacity>
            )}

            {(state === "loading" || state === "verifying" || state === "submitting") && (
              <TouchableOpacity style={[styles.button, styles.buttonDisabled]} disabled>
                <Text style={styles.buttonText}>Verifying...</Text>
              </TouchableOpacity>
            )}

            {(state === "error" || state === "no_enrollment" || state === "biometric_mismatch") && (
              <TouchableOpacity style={styles.button} onPress={handleStartVerify}>
                <Text style={styles.buttonText}>Retry</Text>
              </TouchableOpacity>
            )}

            {state === "wrong_device" && (
              <TouchableOpacity style={[styles.button, styles.buttonDisabled]} disabled>
                <Text style={styles.buttonText}>Wrong Device</Text>
              </TouchableOpacity>
            )}

            {state === "success" && (
              <TouchableOpacity style={styles.button} onPress={() => router.back()}>
                <Text style={styles.buttonText}>Done</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>
      )}

      {state === "capturing" && camera.device && (
        <View style={StyleSheet.absoluteFill}>
          <Camera
            ref={camera.cameraRef}
            style={StyleSheet.absoluteFill}
            device={camera.device}
            isActive={true}
            photo={true}
            onInitialized={camera.onInitialized}
          />
          <CaptureOverlay
            step={capture.step}
            faceDetected={capture.step !== "waiting_face"}
          />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#E4E9FA",
  },
  content: {
    flex: 1,
    padding: 16,
  },
  buttonRow: {
    marginTop: 24,
    alignItems: "center",
  },
  button: {
    backgroundColor: "#1B2444",
    borderRadius: 10,
    paddingVertical: 14,
    paddingHorizontal: 32,
    minWidth: 200,
    alignItems: "center",
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: "#FFF",
    fontSize: 16,
    fontWeight: "600",
  },
});
