/**
 * Whether the current instant falls within [voting_opens, voting_closes]
 * for any bound the API provided. ISO 8601 strings from the backend.
 */
export function isWithinScheduledVotingWindow(
    votingOpens?: string | null,
    votingCloses?: string | null,
    nowMs: number = Date.now(),
): boolean {
    if (votingOpens != null && votingOpens !== "") {
        const open = Date.parse(votingOpens);
        if (Number.isNaN(open) || nowMs < open) {
            return false;
        }
    }
    if (votingCloses != null && votingCloses !== "") {
        const close = Date.parse(votingCloses);
        if (Number.isNaN(close) || nowMs > close) {
            return false;
        }
    }
    return true;
}
