/**
 * QR code scanner component using expo-camera's barcode scanning.
 */

import React, { useState } from "react";
import { View, Text, StyleSheet, Dimensions } from "react-native";
import { CameraView } from "expo-camera";

const { width: SCREEN_WIDTH } = Dimensions.get("window");
const SCAN_SIZE = SCREEN_WIDTH * 0.7;

interface QRScannerProps {
  onScan: (data: string) => void;
}

export default function QRScanner({ onScan }: QRScannerProps) {
  const [scanned, setScanned] = useState(false);

  const handleBarCodeScanned = ({ data }: { data: string }) => {
    if (scanned) return;
    setScanned(true);
    onScan(data);
    // Reset after a short delay to allow re-scanning
    setTimeout(() => setScanned(false), 3000);
  };

  return (
    <View style={styles.container}>
      <CameraView
        style={StyleSheet.absoluteFill}
        facing="back"
        barcodeScannerSettings={{
          barcodeTypes: ["qr"],
        }}
        onBarcodeScanned={handleBarCodeScanned}
      />

      {/* Scan area overlay */}
      <View style={styles.overlay}>
        <View style={styles.topOverlay} />
        <View style={styles.middleRow}>
          <View style={styles.sideOverlay} />
          <View style={styles.scanArea}>
            {/* Corner markers */}
            <View style={[styles.corner, styles.topLeft]} />
            <View style={[styles.corner, styles.topRight]} />
            <View style={[styles.corner, styles.bottomLeft]} />
            <View style={[styles.corner, styles.bottomRight]} />
          </View>
          <View style={styles.sideOverlay} />
        </View>
        <View style={styles.bottomOverlay}>
          <Text style={styles.hint}>
            Scan the QR code shown on the voting website
          </Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#000",
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
  },
  topOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.6)",
  },
  middleRow: {
    flexDirection: "row",
    height: SCAN_SIZE,
  },
  sideOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.6)",
  },
  scanArea: {
    width: SCAN_SIZE,
    height: SCAN_SIZE,
  },
  bottomOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.6)",
    alignItems: "center",
    paddingTop: 24,
  },
  hint: {
    color: "#FFF",
    fontSize: 15,
    textAlign: "center",
    maxWidth: "80%",
  },
  corner: {
    position: "absolute",
    width: 24,
    height: 24,
    borderColor: "#FFF",
  },
  topLeft: {
    top: 0, left: 0,
    borderTopWidth: 3, borderLeftWidth: 3,
  },
  topRight: {
    top: 0, right: 0,
    borderTopWidth: 3, borderRightWidth: 3,
  },
  bottomLeft: {
    bottom: 0, left: 0,
    borderBottomWidth: 3, borderLeftWidth: 3,
  },
  bottomRight: {
    bottom: 0, right: 0,
    borderBottomWidth: 3, borderRightWidth: 3,
  },
});
