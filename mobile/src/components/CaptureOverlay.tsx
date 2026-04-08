/**
 * Camera overlay with oval guide, step indicator, and instructions.
 */

import React from "react";
import { View, Text, StyleSheet, Dimensions } from "react-native";
import { CaptureStep } from "../hooks/useBiometricCapture";

const { width: SCREEN_WIDTH } = Dimensions.get("window");

interface CaptureOverlayProps {
  step: CaptureStep;
  faceDetected?: boolean;
  headTurnProgress?: number;
}

const STEP_LABELS: Record<CaptureStep, string> = {
  loading: "Preparing...",
  waiting_face: "Position your face in the oval",
  waiting_blink: "Blink naturally to confirm liveness",
  extracting_face: "Capturing face... hold still",
  turn_head: "Turn your head LEFT to show your ear",
  extracting_ear: "Capturing ear... hold still",
  done: "Capture complete!",
  error: "Something went wrong",
};

export default function CaptureOverlay({ step, faceDetected, headTurnProgress }: CaptureOverlayProps) {
  const showOval = step !== "loading" && step !== "done" && step !== "error";
  const ovalColor = faceDetected ? "rgba(34,197,94,0.8)" : "rgba(255,255,255,0.6)";

  const stepNum =
    step === "loading" ? 0 :
    step === "waiting_face" || step === "waiting_blink" ? 1 :
    step === "extracting_face" ? 2 :
    step === "turn_head" || step === "extracting_ear" ? 3 : 4;

  return (
    <View style={styles.container} pointerEvents="none">
      {/* Step progress bar */}
      <View style={styles.progressContainer}>
        {[
          { label: "Liveness", num: 1 },
          { label: "Face", num: 2 },
          { label: "Ear", num: 3 },
        ].map(({ label, num }) => (
          <View key={label} style={styles.progressItem}>
            <View style={[
              styles.progressBar,
              {
                backgroundColor:
                  num < stepNum ? "#22C55E" :
                  num === stepNum ? "#1B2444" : "#E5E7EB",
              },
            ]} />
            <Text style={[
              styles.progressLabel,
              { fontWeight: num === stepNum ? "600" : "400" },
            ]}>
              {label}
            </Text>
          </View>
        ))}
      </View>

      {/* Oval guide */}
      {showOval && (
        <View style={styles.ovalContainer}>
          <View style={[styles.oval, { borderColor: ovalColor }]} />
        </View>
      )}

      {/* Instruction text */}
      <View style={styles.instructionContainer}>
        <View style={styles.instructionBadge}>
          <Text style={styles.instructionText}>
            {STEP_LABELS[step]}
          </Text>
        </View>
      </View>

      {/* Head turn progress */}
      {step === "turn_head" && headTurnProgress !== undefined && (
        <View style={styles.turnProgressContainer}>
          <View style={styles.turnProgressBg}>
            <View style={[
              styles.turnProgressFill,
              { width: `${headTurnProgress}%` },
            ]} />
          </View>
          <Text style={styles.turnCountdown}>
            Capturing in {Math.max(0, Math.ceil(4 - (headTurnProgress / 100) * 4))}s
          </Text>
        </View>
      )}

      {/* Arrow hint */}
      {step === "turn_head" && (headTurnProgress ?? 0) < 50 && (
        <View style={styles.arrowContainer}>
          <Text style={styles.arrow}>←</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
  },
  progressContainer: {
    flexDirection: "row",
    gap: 4,
    paddingHorizontal: 16,
    paddingTop: 12,
  },
  progressItem: {
    flex: 1,
    alignItems: "center",
  },
  progressBar: {
    height: 5,
    borderRadius: 3,
    width: "100%",
  },
  progressLabel: {
    fontSize: 11,
    color: "#FFF",
    marginTop: 2,
  },
  ovalContainer: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: "center",
    alignItems: "center",
  },
  oval: {
    width: SCREEN_WIDTH * 0.55,
    height: SCREEN_WIDTH * 0.75,
    borderRadius: SCREEN_WIDTH * 0.4,
    borderWidth: 3,
    borderStyle: "dashed",
  },
  instructionContainer: {
    position: "absolute",
    bottom: 100,
    left: 0,
    right: 0,
    alignItems: "center",
  },
  instructionBadge: {
    backgroundColor: "rgba(0,0,0,0.75)",
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 8,
    maxWidth: "85%",
  },
  instructionText: {
    color: "#FFF",
    fontSize: 14,
    textAlign: "center",
  },
  turnProgressContainer: {
    position: "absolute",
    bottom: 60,
    left: 20,
    right: 20,
  },
  turnProgressBg: {
    height: 6,
    borderRadius: 3,
    backgroundColor: "rgba(255,255,255,0.25)",
  },
  turnProgressFill: {
    height: "100%",
    borderRadius: 3,
    backgroundColor: "#22C55E",
  },
  turnCountdown: {
    color: "#FFF",
    fontSize: 12,
    textAlign: "center",
    marginTop: 4,
  },
  arrowContainer: {
    position: "absolute",
    top: "50%",
    right: 16,
  },
  arrow: {
    fontSize: 36,
    color: "rgba(255,255,255,0.7)",
  },
});
