// Voting Step4: Candidate Selection

import ProgressBar from "./progressBar";
import { getVoterPageContentWrapperStyle, getCardStyle, getStepTitleStyle, getStepDescStyle } from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";
import PrimaryButton from "../../../components/PrimaryButton";

const CANDIDATES = [
    { id: 1, name: "John Doe" },
    { id: 2, name: "Jane Smith" },
    { id: 3, name: "Bob Johnson" },
    { id: 4, name: "Alice Williams" },
    { id: 5, name: "Charlie Brown" },
] // TODO: Replace with actual candidates

function CandidateSelection({next, state, setState}: {next: () => void, state: any, setState: (state: any) => void}) {
    const { theme } = useTheme();
    return (
        <div style={{ ...getVoterPageContentWrapperStyle(theme), maxWidth: "100%", margin: "0 auto" }}>
            <div style={{...getCardStyle(theme), marginBottom: "1.75rem"}}>
                <ProgressBar step={4} theme={theme} />
            </div>
            <h1 style={getStepTitleStyle(theme)}>Candidate Selection</h1>
            <p style={getStepDescStyle(theme)}>Please select the candidate you wish to vote for.</p>
            {CANDIDATES.map(c => {
                const selected = state.candidate === c.id;
                return (
                    <label
                        key={c.id}
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
                            name="candidate"
                            value={c.id}
                            checked={!!selected}
                            onChange={() => setState({...state, candidate: c.id})}
                            style={{ accentColor: theme.colors.button }}
                        />
                        <span style={{ fontSize: theme.fontSizes.base, color: theme.colors.text.primary }}>{c.name}</span>
                    </label>
                );
            })}
            <div style={{ marginTop: "1.75rem", display: "flex", justifyContent: "center" }}>
                <PrimaryButton onClick={next}>Next</PrimaryButton>
            </div>
        </div>
    )
} export default CandidateSelection;