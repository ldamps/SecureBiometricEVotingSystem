/**
 * Home screen — QR code scanner.
 *
 * Scans QR codes from the desktop voting website and routes to
 * either the enrollment or verification screen.
 */

import React, { useCallback, useState } from "react";
import { View, Text, StyleSheet, TouchableOpacity, Alert } from "react-native";
import { useCameraPermissions } from "expo-camera";
import { useRouter } from "expo-router";
import QRScanner from "../src/components/QRScanner";
import { parseQRCode } from "../src/services/qr-parser.service";

export default function HomeScreen() {
  const router = useRouter();
  const [permission, requestPermission] = useCameraPermissions();
  const [scanning, setScanning] = useState(true);

  const handleScan = useCallback(
    (data: string) => {
      const action = parseQRCode(data);

      switch (action.type) {
        case "enroll":
          setScanning(false);
          router.push(`/enroll?voter_id=${action.voterId}`);
          setTimeout(() => setScanning(true), 1000);
          break;

        case "verify":
          setScanning(false);
          router.push(
            `/verify?voter_id=${action.voterId}&challenge_id=${action.challengeId}`,
          );
          setTimeout(() => setScanning(true), 1000);
          break;

        case "unknown":
          Alert.alert(
            "Unrecognised QR Code",
            "This QR code is not from the e-voting platform. Please scan the QR code shown on the voting website.",
          );
          break;
      }
    },
    [router],
  );

  if (!permission?.granted) {
    return (
      <View style={styles.permissionContainer}>
        <Text style={styles.permissionTitle}>Camera Access Required</Text>
        <Text style={styles.permissionText}>
          This app needs camera access to scan QR codes and capture your
          biometrics for secure identity verification.
        </Text>
        <Text style={styles.permissionText}>
          Your biometric data is stored only on this device and never
          sent to any server.
        </Text>
        <TouchableOpacity style={styles.button} onPress={requestPermission}>
          <Text style={styles.buttonText}>Grant Camera Access</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {scanning && <QRScanner onScan={handleScan} />}

      {/* Bottom info bar */}
      <View style={styles.infoBar}>
        <Text style={styles.infoTitle}>Biometric Companion App</Text>
        <Text style={styles.infoText}>
          Scan the QR code on the voting website to enrol or verify your identity.
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#000",
  },
  permissionContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 32,
    backgroundColor: "#E4E9FA",
  },
  permissionTitle: {
    fontSize: 22,
    fontWeight: "700",
    color: "#1B2444",
    marginBottom: 16,
    textAlign: "center",
  },
  permissionText: {
    fontSize: 15,
    color: "#364150",
    textAlign: "center",
    lineHeight: 22,
    marginBottom: 12,
  },
  button: {
    backgroundColor: "#1B2444",
    borderRadius: 10,
    paddingVertical: 14,
    paddingHorizontal: 32,
    marginTop: 20,
  },
  buttonText: {
    color: "#FFF",
    fontSize: 16,
    fontWeight: "600",
  },
  infoBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: "rgba(27,36,68,0.95)",
    padding: 20,
    paddingBottom: 40,
  },
  infoTitle: {
    color: "#FFF",
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 4,
  },
  infoText: {
    color: "rgba(255,255,255,0.7)",
    fontSize: 13,
    lineHeight: 18,
  },
});
