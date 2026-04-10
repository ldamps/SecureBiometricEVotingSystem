/**
 * Status card component for displaying messages during biometric flows.
 */

import React from "react";
import { View, Text, StyleSheet } from "react-native";

interface StatusCardProps {
  title: string;
  message: string;
  error?: string | null;
  variant?: "default" | "success" | "error";
}

export default function StatusCard({ title, message, error, variant = "default" }: StatusCardProps) {
  const borderColor =
    variant === "success" ? "#22C55E" :
    variant === "error" ? "#EF4444" : "#C7CDE8";

  return (
    <View style={[styles.card, { borderLeftColor: borderColor }]}>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.message}>{message}</Text>
      {error && <Text style={styles.error}>{error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 16,
    marginVertical: 8,
    borderLeftWidth: 4,
    borderLeftColor: "#C7CDE8",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  title: {
    fontSize: 16,
    fontWeight: "600",
    color: "#0F172A",
    marginBottom: 4,
  },
  message: {
    fontSize: 14,
    color: "#364150",
    lineHeight: 20,
  },
  error: {
    fontSize: 13,
    color: "#EF4444",
    marginTop: 8,
    fontWeight: "500",
  },
});
