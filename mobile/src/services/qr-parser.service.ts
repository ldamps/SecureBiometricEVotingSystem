/**
 * Parse QR code deep-link URLs from the desktop voting site.
 *
 * Deep-link enrollment:  evoting://enroll?voter_id=UUID
 * Deep-link verify:      evoting://verify?voter_id=UUID&challenge_id=UUID
 *
 * Legacy web URLs are also accepted for backwards compatibility:
 *   https://host/biometric/enroll?voter_id=UUID
 *   https://host/biometric/verify?voter_id=UUID&challenge_id=UUID
 */

export type QRAction =
  | { type: "enroll"; voterId: string }
  | { type: "verify"; voterId: string; challengeId: string }
  | { type: "unknown" };

export function parseQRCode(data: string): QRAction {
  try {
    const url = new URL(data);
    const voterId = url.searchParams.get("voter_id");

    if (!voterId) return { type: "unknown" };

    // For deep links (evoting://enroll, evoting://verify) the "host" is
    // the action name.  For web URLs, check the pathname.
    const action = url.hostname || url.pathname;

    if (action.includes("enroll")) {
      return { type: "enroll", voterId };
    }

    if (action.includes("verify")) {
      const challengeId = url.searchParams.get("challenge_id");
      if (!challengeId) return { type: "unknown" };
      return { type: "verify", voterId, challengeId };
    }

    return { type: "unknown" };
  } catch {
    return { type: "unknown" };
  }
}
