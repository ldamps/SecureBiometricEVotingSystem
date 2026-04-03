// Voting Step1: Election Selection
import {
    getCardStyle,
    getVoterPageContentWrapperStyle,
    getStepTitleStyle,
    getStepDescStyle,
} from "../../../styles/ui";
import ProgressBar from "../../voter/components/progressBar";
import { useTheme } from "../../../styles/ThemeContext";
import { PrimaryButton } from "../../../styles/ui";
import { ElectionApiRepository } from "../repositories/election-api.repository";
import { Election } from "../model/election.model";
import { ReferendumApiRepository } from "../../referendum/repositories/referendum-api.repository";
import { Referendum } from "../../referendum/model/referendum.model";
import { VoterApiRepository } from "../../voter/repositories/voter-api.repository";
import { useEffect, useState, type CSSProperties } from "react";

const electionApiRepository = new ElectionApiRepository();
const referendumApiRepository = new ReferendumApiRepository();
const voterApiRepository = new VoterApiRepository();

function useMinWidthMd(breakpointPx: number) {
    const [matches, setMatches] = useState(false);

    useEffect(() => {
        if (typeof window === "undefined") return;
        const mq = window.matchMedia(`(min-width: ${breakpointPx}px)`);
        const update = () => setMatches(mq.matches);
        update();
        mq.addEventListener("change", update);
        return () => mq.removeEventListener("change", update);
    }, [breakpointPx]);

    return matches;
}

function ElectionSelection({
    next,
    state,
    setState,
}: {
    next: () => void;
    state: any;
    setState: (state: any) => void;
}) {
    const { theme } = useTheme();
    const isTwoColumn = useMinWidthMd(theme.breakpoints.md);
    const [elections, setElections] = useState<Election[]>([]);
    const [referendums, setReferendums] = useState<Referendum[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const constituencyId: string | undefined = state.constituencyId;
    const voterId: string | undefined = state.voterId;

    useEffect(() => {
        let cancelled = false;
        setLoading(true);

        const electionsPromise = constituencyId
            ? electionApiRepository.listOpenElectionsForConstituency(constituencyId)
            : electionApiRepository.listOpenElections();

        const referendumsPromise = constituencyId
            ? referendumApiRepository.listOpenReferendumsForConstituency(constituencyId)
            : referendumApiRepository.listOpenReferendums();

        const ledgerPromise = voterId
            ? voterApiRepository.listLedgerEntries(voterId)
            : Promise.resolve([]);

        Promise.all([electionsPromise, referendumsPromise, ledgerPromise])
            .then(([openElections, openReferendums, ledgerEntries]) => {
                if (cancelled) return;
                const votedElectionIds = new Set(
                    ledgerEntries.filter((l) => l.election_id).map((l) => l.election_id),
                );
                const votedReferendumIds = new Set(
                    ledgerEntries.filter((l) => l.referendum_id).map((l) => l.referendum_id),
                );
                setElections(openElections.filter((e) => !votedElectionIds.has(e.id)));
                setReferendums(openReferendums.filter((r) => !votedReferendumIds.has(r.id)));
                setError(null);
            })
            .catch((err: Error) => {
                if (!cancelled) {
                    setError(err.message || "Failed to load elections and referendums.");
                }
            })
            .finally(() => {
                if (!cancelled) setLoading(false);
            });
        return () => {
            cancelled = true;
        };
    }, [constituencyId, voterId]);

    const hasSelection = Boolean(state.election) || Boolean(state.referendum);

    const columnShellStyle: CSSProperties = {
        flex: isTwoColumn ? "1 1 0" : "1 1 auto",
        minWidth: 0,
        display: "flex",
        flexDirection: "column",
        gap: theme.spacing.md,
    };

    const sectionTitleStyle: CSSProperties = {
        fontSize: theme.fontSizes.lg,
        fontWeight: theme.fontWeights.semibold,
        color: theme.colors.text.primary,
        margin: 0,
    };

    return (
        <div style={{ ...getVoterPageContentWrapperStyle(theme), maxWidth: "100%", margin: "0 auto" }}>
            <div style={{ ...getCardStyle(theme), marginBottom: "1.75rem" }}>
                <ProgressBar step={3} theme={theme} />
            </div>
            <h2 style={getStepTitleStyle(theme)}>Select an Election or Referendum</h2>
            <p style={getStepDescStyle(theme)}>Please select the election or referendum you wish to vote in.</p>
            {error && (
                <p style={{ color: theme.colors.status.error, marginBottom: "1rem" }}>{error}</p>
            )}
            {loading && !error && (
                <p style={{ color: theme.colors.text.secondary, marginBottom: "1rem" }}>Loading…</p>
            )}
            {!loading && !error && elections.length === 0 && referendums.length === 0 && (
                <p style={{ color: theme.colors.text.secondary, marginBottom: "1rem" }}>
                    No open elections or referendums are available right now.
                </p>
            )}
            {!loading && !error && (elections.length > 0 || referendums.length > 0) && (
                <div
                    style={{
                        display: "flex",
                        flexDirection: isTwoColumn ? "row" : "column",
                        gap: isTwoColumn ? theme.spacing.xl : theme.spacing.lg,
                        alignItems: "stretch",
                    }}
                >
                    <div style={columnShellStyle}>
                        <h3 style={sectionTitleStyle}>Elections</h3>
                        {elections.length === 0 ? (
                            <p style={{ color: theme.colors.text.secondary, margin: 0 }}>
                                No open elections right now.
                            </p>
                        ) : (
                            elections.map((election) => {
                                const selected = state.election === election.id;
                                return (
                                    <label
                                        key={election.id}
                                        style={{
                                            ...getCardStyle(theme),
                                            marginBottom: 0,
                                            display: "flex",
                                            alignItems: "center",
                                            gap: theme.spacing.md,
                                            cursor: "pointer",
                                        }}
                                    >
                                        <input
                                            type="radio"
                                            name="ballot"
                                            value={election.id}
                                            checked={!!selected}
                                            onChange={() =>
                                                setState({ ...state, election: election.id, referendum: "" })
                                            }
                                            style={{ accentColor: theme.colors.button }}
                                        />
                                        <span
                                            style={{
                                                fontSize: theme.fontSizes.base,
                                                color: theme.colors.text.primary,
                                            }}
                                        >
                                            {election.title}
                                        </span>
                                    </label>
                                );
                            })
                        )}
                    </div>
                    <div style={columnShellStyle}>
                        <h3 style={sectionTitleStyle}>Referendums</h3>
                        {referendums.length === 0 ? (
                            <p style={{ color: theme.colors.text.secondary, margin: 0 }}>
                                No open referendums right now.
                            </p>
                        ) : (
                            referendums.map((referendum) => {
                                const selected = state.referendum === referendum.id;
                                return (
                                    <label
                                        key={referendum.id}
                                        style={{
                                            ...getCardStyle(theme),
                                            marginBottom: 0,
                                            display: "flex",
                                            alignItems: "center",
                                            gap: theme.spacing.md,
                                            cursor: "pointer",
                                        }}
                                    >
                                        <input
                                            type="radio"
                                            name="ballot"
                                            value={referendum.id}
                                            checked={!!selected}
                                            onChange={() =>
                                                setState({ ...state, referendum: referendum.id, election: "" })
                                            }
                                            style={{ accentColor: theme.colors.button }}
                                        />
                                        <span
                                            style={{
                                                fontSize: theme.fontSizes.base,
                                                color: theme.colors.text.primary,
                                            }}
                                        >
                                            {referendum.title}
                                        </span>
                                    </label>
                                );
                            })
                        )}
                    </div>
                </div>
            )}

            <div style={{ marginTop: "1.75rem", display: "flex", justifyContent: "center" }}>
                <PrimaryButton onClick={next} disabled={!hasSelection}>
                    Next
                </PrimaryButton>
            </div>
        </div>
    );
}
export default ElectionSelection;
