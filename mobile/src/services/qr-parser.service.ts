/**
 * Parse QR code URLs from the desktop voting site.
 *
 * Enrollment URL:  https://host/biometric/enroll?voter_id=UUID
 * Verify URL:      https://host/biometric/verify?voter_id=UUID&challenge_id=UUID
 */

export type QRAction =
  | { type: "enroll"; voterId: string }
  | { type: "verify"; voterId: string; challengeId: string }
  | { type: "unknown" };

export function parseQRCode(data: string): QRAction {
  try {
    const url = new URL(data);
    const path = url.pathname;
    const voterId = url.searchParams.get("voter_id");

    if (!voterId) return { type: "unknown" };

    if (path.includes("/biometric/enroll") || path.includes("/enroll")) {
      return { type: "enroll", voterId };
    }

    if (path.includes("/biometric/verify") || path.includes("/verify")) {
      const challengeId = url.searchParams.get("challenge_id");
      if (!challengeId) return { type: "unknown" };
      return { type: "verify", voterId, challengeId };
    }

    return { type: "unknown" };
  } catch {
    return { type: "unknown" };
  }
}
