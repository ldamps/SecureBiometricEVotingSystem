// Voting Step1: Election Selection
import { getCardStyle, getVoterPageContentWrapperStyle, getStepTitleStyle, getStepDescStyle } from "../../../styles/ui";
import ProgressBar from "./progressBar";
import { useTheme } from "../../../styles/ThemeContext";
import { PrimaryButton } from "../../../styles/ui";
import { ElectionApiRepository } from "../repositories/election-api.repository";
import { Election, ElectionStatus } from "../model/election.model";
import { useEffect, useState } from "react";

const electionApiRepository = new ElectionApiRepository();

async function getElections(): Promise<Election[]> {
    const elections = await electionApiRepository.listElections();
    return elections.filter((election) => election.status === ElectionStatus.OPEN);
}

function ElectionSelection({next, state, setState}: {next: () => void, state: any, setState: (state: any) => void}) {
    const { theme } = useTheme();
    const [elections, setElections] = useState<Election[]>([]);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        getElections()
            .then(setElections)
            .catch((err: Error) => {
                setError(err.message || "Failed to load elections.");
            });
    }, []);

    return (
        <div style={{ ...getVoterPageContentWrapperStyle(theme), maxWidth: "100%", margin: "0 auto" }}>
            <div style={{...getCardStyle(theme), marginBottom: "1.75rem"}}>
                <ProgressBar step={1} theme={theme} />
            </div>
            <h2 style={getStepTitleStyle(theme)}>Select an Election</h2>
            <p style={getStepDescStyle(theme)}>Please select the election you wish to vote in.</p>
            {error && (
                <p style={{ color: theme.colors.status.error, marginBottom: "1rem" }}>{error}</p>
            )}
            {!error && elections.length === 0 && (
                <p style={{ color: theme.colors.text.secondary, marginBottom: "1rem" }}>
                    No open elections are available right now.
                </p>
            )}
            {elections.map(election => {
                const selected = state.election === election.id;
                return (
                    <label
                        key={election.id}
                        style={{
                            ...getCardStyle(theme),
                            marginBottom: "1rem",
                            display: "flex",
                            alignItems: "center",
                            gap: theme.spacing.md,
                            cursor: "pointer",
                        }}
                    >
                        <input
                            type="radio"
                            name="election"
                            value={election.id}
                            checked={!!selected}
                            onChange={() => setState({...state, election: election.id})}
                            style={{ accentColor: theme.colors.button }}
                        />
                        <span style={{ fontSize: theme.fontSizes.base, color: theme.colors.text.primary }}>{election.title}</span>
                    </label>
                );
            })}
            <div style={{ marginTop: "1.75rem", display: "flex", justifyContent: "center" }}>
                <PrimaryButton onClick={next} disabled={!state.election}>Next</PrimaryButton>
            </div>
        </div>
    )
} export default ElectionSelection;