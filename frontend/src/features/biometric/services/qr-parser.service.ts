/**
 * Parse a QR code string into a typed biometric action.
 *
 * Accepts web URLs of the form:
 *   - .../biometric/enroll?voter_id=<uuid>
 *   - .../biometric/verify?voter_id=<uuid>&challenge_id=<uuid>
 */

export type QRAction =
  | { type: "enroll"; voterId: string }
  | { type: "verify"; voterId: string; challengeId: string }
  | { type: "unknown" };

export function parseQRCode(raw: string): QRAction {
  try {
    const url = new URL(raw);

    if (url.pathname.endsWith("/biometric/enroll")) {
      const voterId = url.searchParams.get("voter_id");
      if (voterId) return { type: "enroll", voterId };
    }

    if (url.pathname.endsWith("/biometric/verify")) {
      const voterId = url.searchParams.get("voter_id");
      const challengeId = url.searchParams.get("challenge_id");
      if (voterId && challengeId) return { type: "verify", voterId, challengeId };
    }
  } catch {
    // Not a valid URL
  }

  return { type: "unknown" };
}
