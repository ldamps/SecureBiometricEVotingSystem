/**
 * Root layout — app shell with navigation.
 */

import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";

export default function RootLayout() {
  return (
    <>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: "#1B2444" },
          headerTintColor: "#FFF",
          headerTitleStyle: { fontWeight: "600" },
        }}
      >
        <Stack.Screen
          name="index"
          options={{ title: "E-Voting Biometric" }}
        />
        <Stack.Screen
          name="enroll"
          options={{ title: "Biometric Enrollment" }}
        />
        <Stack.Screen
          name="verify"
          options={{ title: "Biometric Verification" }}
        />
      </Stack>
    </>
  );
}
