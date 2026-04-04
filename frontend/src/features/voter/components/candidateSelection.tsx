// Voting Step: Candidate Selection (supports FPTP, AV, STV, AMS)

import { useState, useEffect } from "react";
import ProgressBar from "./progressBar";
import {
    getVoterPageContentWrapperStyle,
    getCardStyle,
    getStepTitleStyle,
    getStepDescStyle,
    getStepLabelStyle,
    PrimaryButton,
} from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";
import { ElectionApiRepository } from "../../election/repositories/election-api.repository";
import { CandidateApiRepository, PartyApiRepository } from "../../election/repositories/candidate-api.repository";
import type { Election } from "../../election/model/election.model";
import type { Candidate, Party } from "../../election/model/candidate.model";
import { AllocationMethod } from "../../election/model/election.model";

const electionApi = new ElectionApiRepository();
const candidateApi = new CandidateApiRepository();
const partyApi = new PartyApiRepository();

// ---------------------------------------------------------------------------
// Sub-components for each electoral system
// ---------------------------------------------------------------------------

/** FPTP: select exactly one candidate */
function FPTPBallot({
    candidates,
    partyMap,
    selected,
    onSelect,
    theme,
}: {
    candidates: Candidate[];
    partyMap: Map<string, Party>;
    selected: string;
    onSelect: (id: string) => void;
    theme: any;
}) {
    return (
        <>
            <p style={getStepDescStyle(theme)}>
                Select <strong>one</strong> candidate. The candidate with the most votes wins.
            </p>
            {candidates.map((c) => {
                const party = partyMap.get(c.party_id);
                return (
                    <label
                        key={c.id}
                        style={{
                            ...getCardStyle(theme),
                            marginBottom: "0.75rem",
                            display: "flex",
                            alignItems: "center",
                            gap: theme.spacing.md,
                            cursor: "pointer",
                            border: selected === c.id ? `2px solid ${theme.colors.primary || theme.colors.button}` : undefined,
                        }}
                    >
                        <input
                            type="radio"
                            name="fptp-candidate"
                            checked={selected === c.id}
                            onChange={() => onSelect(c.id)}
                            style={{ accentColor: theme.colors.button }}
                        />
                        <div>
                            <span style={{ fontSize: theme.fontSizes.base, fontWeight: 600, color: theme.colors.text.primary }}>
                                {c.first_name} {c.last_name}
                            </span>
                            {party && (
                                <span style={{ fontSize: theme.fontSizes.sm, color: theme.colors.text.secondary, marginLeft: theme.spacing.sm }}>
                                    — {party.party_name}
                                </span>
                            )}
                        </div>
                    </label>
                );
            })}
        </>
    );
}

/** Ranked ballot for AV and STV: rank candidates by preference */
function RankedBallot({
    candidates,
    partyMap,
    rankings,
    onSetRank,
    onClearRank,
    theme,
    description,
}: {
    candidates: Candidate[];
    partyMap: Map<string, Party>;
    rankings: Record<string, number>;
    onSetRank: (candidateId: string, rank: number) => void;
    onClearRank: (candidateId: string) => void;
    theme: any;
    description: string;
}) {
    const nextRank = candidates.length > 0
        ? Math.max(0, ...Object.values(rankings)) + 1
        : 1;

    return (
        <>
            <p style={getStepDescStyle(theme)}>{description}</p>
            {candidates.map((c) => {
                const party = partyMap.get(c.party_id);
                const rank = rankings[c.id];
                const hasRank = rank !== undefined;
                return (
                    <div
                        key={c.id}
                        style={{
                            ...getCardStyle(theme),
                            marginBottom: "0.75rem",
                            display: "flex",
                            alignItems: "center",
                            gap: theme.spacing.md,
                            border: hasRank ? `2px solid ${theme.colors.primary || theme.colors.button}` : undefined,
                        }}
                    >
                        <div
                            style={{
                                width: "2.5rem",
                                height: "2.5rem",
                                borderRadius: "50%",
                                backgroundColor: hasRank ? (theme.colors.primary || theme.colors.button) : theme.colors.border,
                                color: hasRank ? "#fff" : theme.colors.text.secondary,
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                fontWeight: 700,
                                fontSize: theme.fontSizes.base,
                                flexShrink: 0,
                                cursor: "pointer",
                            }}
                            onClick={() => {
                                if (hasRank) {
                                    onClearRank(c.id);
                                } else {
                                    onSetRank(c.id, nextRank);
                                }
                            }}
                            title={hasRank ? "Click to remove preference" : `Click to set as preference ${nextRank}`}
                        >
                            {hasRank ? rank : "—"}
                        </div>
                        <div style={{ flex: 1 }}>
                            <span style={{ fontSize: theme.fontSizes.base, fontWeight: 600, color: theme.colors.text.primary }}>
                                {c.first_name} {c.last_name}
                            </span>
                            {party && (
                                <span style={{ fontSize: theme.fontSizes.sm, color: theme.colors.text.secondary, marginLeft: theme.spacing.sm }}>
                                    — {party.party_name}
                                </span>
                            )}
                        </div>
                    </div>
                );
            })}
            <p style={{ fontSize: theme.fontSizes.sm, color: theme.colors.text.secondary, marginTop: theme.spacing.sm }}>
                Click a circle to assign the next preference. Click again to remove it. At least your first preference is required.
            </p>
        </>
    );
}

/** AMS: two votes — constituency candidate + regional party */
function AMSBallot({
    candidates,
    parties,
    partyMap,
    selectedCandidate,
    selectedParty,
    onSelectCandidate,
    onSelectParty,
    theme,
}: {
    candidates: Candidate[];
    parties: Party[];
    partyMap: Map<string, Party>;
    selectedCandidate: string;
    selectedParty: string;
    onSelectCandidate: (id: string) => void;
    onSelectParty: (id: string) => void;
    theme: any;
}) {
    return (
        <>
            <p style={getStepDescStyle(theme)}>
                You have <strong>two votes</strong>. First, select your constituency candidate. Then, select a party for the regional list.
            </p>

            {/* Constituency vote */}
            <h3 style={{ ...getStepLabelStyle(theme), marginBottom: theme.spacing.sm, marginTop: theme.spacing.lg }}>
                Vote 1: Constituency Candidate
            </h3>
            {candidates.map((c) => {
                const party = partyMap.get(c.party_id);
                return (
                    <label
                        key={c.id}
                        style={{
                            ...getCardStyle(theme),
                            marginBottom: "0.75rem",
                            display: "flex",
                            alignItems: "center",
                            gap: theme.spacing.md,
                            cursor: "pointer",
                            border: selectedCandidate === c.id ? `2px solid ${theme.colors.primary || theme.colors.button}` : undefined,
                        }}
                    >
                        <input
                            type="radio"
                            name="ams-candidate"
                            checked={selectedCandidate === c.id}
                            onChange={() => onSelectCandidate(c.id)}
                            style={{ accentColor: theme.colors.button }}
                        />
                        <div>
                            <span style={{ fontSize: theme.fontSizes.base, fontWeight: 600, color: theme.colors.text.primary }}>
                                {c.first_name} {c.last_name}
                            </span>
                            {party && (
                                <span style={{ fontSize: theme.fontSizes.sm, color: theme.colors.text.secondary, marginLeft: theme.spacing.sm }}>
                                    — {party.party_name}
                                </span>
                            )}
                        </div>
                    </label>
                );
            })}

            {/* Regional party vote */}
            <h3 style={{ ...getStepLabelStyle(theme), marginBottom: theme.spacing.sm, marginTop: theme.spacing.lg }}>
                Vote 2: Regional Party List
            </h3>
            {parties.filter((p) => p.is_active).map((p) => (
                <label
                    key={p.id}
                    style={{
                        ...getCardStyle(theme),
                        marginBottom: "0.75rem",
                        display: "flex",
                        alignItems: "center",
                        gap: theme.spacing.md,
                        cursor: "pointer",
                        border: selectedParty === p.id ? `2px solid ${theme.colors.primary || theme.colors.button}` : undefined,
                    }}
                >
                    <input
                        type="radio"
                        name="ams-party"
                        checked={selectedParty === p.id}
                        onChange={() => onSelectParty(p.id)}
                        style={{ accentColor: theme.colors.button }}
                    />
                    <span style={{ fontSize: theme.fontSizes.base, fontWeight: 600, color: theme.colors.text.primary }}>
                        {p.party_name}
                        {p.abbreviation && (
                            <span style={{ fontWeight: 400, color: theme.colors.text.secondary }}> ({p.abbreviation})</span>
                        )}
                    </span>
                </label>
            ))}
        </>
    );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

function CandidateSelection({
    next,
    back,
    state,
    setState,
}: {
    next: () => void;
    back: () => void;
    state: any;
    setState: (state: any) => void;
}) {
    const { theme } = useTheme();
    const [election, setElection] = useState<Election | null>(null);
    const [candidates, setCandidates] = useState<Candidate[]>([]);
    const [parties, setParties] = useState<Party[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [validationError, setValidationError] = useState<string | null>(null);

    const partyMap = new Map(parties.map((p) => [p.id, p]));
    const method: AllocationMethod | undefined = election?.allocation_method;

    useEffect(() => {
        if (!state.election) return;
        setLoading(true);
        Promise.all([
            electionApi.getElection(state.election),
            candidateApi.listCandidates(state.election),
            partyApi.listParties(),
        ])
            .then(([el, cands, pts]) => {
                setElection(el);
                // Filter to active candidates in voter's constituency (if set)
                const filtered = state.constituencyId
                    ? cands.filter((c) => c.constituency_id === state.constituencyId && c.is_active)
                    : cands.filter((c) => c.is_active);
                setCandidates(filtered);
                setParties(pts);
                setError(null);
            })
            .catch((err: Error) => setError(err.message || "Failed to load election data."))
            .finally(() => setLoading(false));
    }, [state.election, state.constituencyId]);

    // State for each electoral system
    const selectedCandidate: string = state.candidateId || "";
    const selectedParty: string = state.partyId || "";
    const rankings: Record<string, number> = state.rankings || {};

    const setSelectedCandidate = (id: string) => setState({ ...state, candidateId: id });
    const setSelectedParty = (id: string) => setState({ ...state, partyId: id });
    const setRankings = (r: Record<string, number>) => setState({ ...state, rankings: r });

    const handleSetRank = (candidateId: string, rank: number) => {
        setRankings({ ...rankings, [candidateId]: rank });
    };

    const handleClearRank = (candidateId: string) => {
        const cleared = { ...rankings };
        const removedRank = cleared[candidateId];
        delete cleared[candidateId];
        // Reorder ranks to fill gap
        const reordered: Record<string, number> = {};
        for (const [cid, r] of Object.entries(cleared)) {
            reordered[cid] = r > removedRank ? r - 1 : r;
        }
        setRankings(reordered);
    };

    const handleNext = () => {
        setValidationError(null);

        if (method === AllocationMethod.FPTP) {
            if (!selectedCandidate) {
                setValidationError("Please select a candidate.");
                return;
            }
        } else if (method === AllocationMethod.ALTERNATIVE_VOTE || method === AllocationMethod.STV) {
            if (Object.keys(rankings).length === 0) {
                setValidationError("Please rank at least your first preference.");
                return;
            }
        } else if (method === AllocationMethod.AMS) {
            if (!selectedCandidate && !selectedParty) {
                setValidationError("Please select at least one of: a constituency candidate or a regional party.");
                return;
            }
        }

        next();
    };

    return (
        <div style={{ ...getVoterPageContentWrapperStyle(theme), maxWidth: "100%", margin: "0 auto" }}>
            <div style={{ ...getCardStyle(theme), marginBottom: "1.75rem" }}>
                <ProgressBar step={4} theme={theme} />
            </div>

            <h1 style={getStepTitleStyle(theme)}>
                {election ? election.title : "Candidate Selection"}
            </h1>

            {loading && <p style={{ color: theme.colors.text.secondary }}>Loading candidates…</p>}
            {error && <p style={{ color: theme.colors.status.error }}>{error}</p>}

            {!loading && !error && candidates.length === 0 && (
                <p style={{ color: theme.colors.text.secondary }}>
                    No candidates are standing in your constituency for this election.
                </p>
            )}

            {!loading && !error && candidates.length > 0 && method === AllocationMethod.FPTP && (
                <FPTPBallot
                    candidates={candidates}
                    partyMap={partyMap}
                    selected={selectedCandidate}
                    onSelect={setSelectedCandidate}
                    theme={theme}
                />
            )}

            {!loading && !error && candidates.length > 0 && method === AllocationMethod.ALTERNATIVE_VOTE && (
                <RankedBallot
                    candidates={candidates}
                    partyMap={partyMap}
                    rankings={rankings}
                    onSetRank={handleSetRank}
                    onClearRank={handleClearRank}
                    theme={theme}

                    description="Rank the candidates in order of preference. If no candidate wins a majority of first-preference votes, the lowest-ranked candidate is eliminated and their votes redistributed until one candidate secures over 50%."
                />
            )}

            {!loading && !error && candidates.length > 0 && method === AllocationMethod.STV && (
                <RankedBallot
                    candidates={candidates}
                    partyMap={partyMap}
                    rankings={rankings}
                    onSetRank={handleSetRank}
                    onClearRank={handleClearRank}
                    theme={theme}

                    description="Rank the candidates in order of preference. Candidates are elected by reaching a vote quota. Surplus and eliminated votes are redistributed according to your preferences until all seats are filled."
                />
            )}

            {!loading && !error && candidates.length > 0 && method === AllocationMethod.AMS && (
                <AMSBallot
                    candidates={candidates}
                    parties={parties}
                    partyMap={partyMap}
                    selectedCandidate={selectedCandidate}
                    selectedParty={selectedParty}
                    onSelectCandidate={setSelectedCandidate}
                    onSelectParty={setSelectedParty}
                    theme={theme}
                />
            )}

            {validationError && (
                <p style={{ color: theme.colors.status.error, fontSize: "0.875rem", marginTop: "0.75rem" }}>
                    {validationError}
                </p>
            )}

            <div style={{ marginTop: "1.75rem", display: "flex", justifyContent: "center", gap: theme.spacing?.md ?? theme.spacing?.sm ?? "1rem" }}>
                <PrimaryButton onClick={back}>Back</PrimaryButton>
                <PrimaryButton onClick={handleNext} disabled={loading || candidates.length === 0}>
                    Next
                </PrimaryButton>
            </div>
        </div>
    );
}

export default CandidateSelection;
