/**
 * Enrollment screen — captures face + ear biometrics, generates
 * biometric-bound ECDSA keypair, stores templates locally in
 * secure storage, and sends only the public key to the server.
 *
 * Mirrors the web frontend's mobileEnrollPage.tsx.
 */

import React, { useState, useCallback, useEffect } from "react";
import { View, Text, StyleSheet, TouchableOpacity, Alert } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { Camera } from "react-native-vision-camera";

import StatusCard from "../src/components/StatusCard";
import CaptureOverlay from "../src/components/CaptureOverlay";
import { useCamera } from "../src/hooks/useCamera";
import { useBiometricCapture, CaptureResult } from "../src/hooks/useBiometricCapture";
import { generateAndEncryptKeyPair } from "../src/services/biometric-key-encryption.service";
import { storeBiometricData } from "../src/services/secure-storage.service";
import { getDeviceId } from "../src/services/secure-storage.service";
import { BiometricApi } from "../src/services/biometric-api.service";
import { loadFaceModel } from "../src/services/face-recognition.service";
import { loadEarModel } from "../src/services/ear-recognition.service";
import { Platform } from "react-native";

type EnrollState = "ready" | "capturing" | "generating_keys" | "enrolling" | "success" | "error";

export default function EnrollScreen() {
  const { voter_id } = useLocalSearchParams<{ voter_id: string }>();
  const router = useRouter();
  const camera = useCamera();
  const capture = useBiometricCapture("enroll");

  const [state, setState] = useState<EnrollState>("ready");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Pre-load feature extraction models
    loadFaceModel();
    loadEarModel();
  }, []);

  const handleStartEnroll = useCallback(() => {
    setState("capturing");
    setError(null);
  }, []);

  const handleCaptureComplete = useCallback(
    async (result: CaptureResult) => {
      if (!voter_id) return;

      try {
        setState("generating_keys");

        // Generate ECDSA keypair encrypted with biometric-derived key
        const { publicKeyPem, encryptedBundle } = await generateAndEncryptKeyPair(
          result.faceDescriptor,
          result.earDescriptor,
        );

        // Store templates + encrypted key locally in secure storage
        // (iOS Keychain / Android Keystore — survives browser clearing)
        await storeBiometricData({
          voterId: voter_id,
          faceTemplate: Array.from(result.faceDescriptor),
          earTemplate: Array.from(result.earDescriptor),
          encryptedKeyBundle: encryptedBundle,
          enrolledAt: new Date().toISOString(),
        });

        setState("enrolling");

        // Send ONLY the public key and encrypted bundle to the server.
        // No biometric templates are sent.
        const deviceId = await getDeviceId();
        await BiometricApi.enrollDevice({
          voter_id,
          public_key_pem: publicKeyPem,
          device_id: deviceId,
          modalities: "face+ear",
          device_label: `${Platform.OS} ${Platform.Version}`,
          encrypted_key_bundle: JSON.stringify(encryptedBundle),
        });

        setState("success");
      } catch (err: any) {
        setError(err.message || "Enrollment failed. Please try again.");
        setState("error");
      }
    },
    [voter_id],
  );

  // When capture hook produces a result, process it
  useEffect(() => {
    if (capture.result) {
      handleCaptureComplete(capture.result);
    }
  }, [capture.result, handleCaptureComplete]);

  const messages: Record<EnrollState, { title: string; message: string }> = {
    ready: {
      title: "Biometric Enrollment",
      message:
        "This device will be linked to your voter account. " +
        "Your face and ear biometrics will be captured and stored " +
        "only on this device — the server only receives a cryptographic public key.",
    },
    capturing: { title: "Capturing", message: "" },
    generating_keys: {
      title: "Generating Keys",
      message: "Creating biometric-bound encryption keys. Your private signing key is being encrypted with your biometric features.",
    },
    enrolling: {
      title: "Enrolling",
      message: "Registering your device with the voting platform...",
    },
    success: {
      title: "Enrollment Complete",
      message:
        "Your device has been successfully enrolled! Your face and ear " +
        "biometrics are stored securely on this device only. You can now " +
        "close this screen and return to the registration page on your computer.",
    },
    error: {
      title: "Error",
      message: "Something went wrong during enrollment.",
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
            variant={state === "success" ? "success" : state === "error" ? "error" : "default"}
          />

          <View style={styles.buttonRow}>
            {state === "ready" && (
              <TouchableOpacity style={styles.button} onPress={handleStartEnroll}>
                <Text style={styles.buttonText}>Start Enrollment</Text>
              </TouchableOpacity>
            )}

            {(state === "generating_keys" || state === "enrolling") && (
              <TouchableOpacity style={[styles.button, styles.buttonDisabled]} disabled>
                <Text style={styles.buttonText}>
                  {state === "generating_keys" ? "Generating keys..." : "Enrolling..."}
                </Text>
              </TouchableOpacity>
            )}

            {state === "error" && (
              <TouchableOpacity style={styles.button} onPress={handleStartEnroll}>
                <Text style={styles.buttonText}>Retry</Text>
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
