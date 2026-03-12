// Voting Step1: Election Selection
import { getCardStyle, getVoterPageContentWrapperStyle, getStepTitleStyle, getStepDescStyle } from "../../../styles/ui";
import ProgressBar from "./progressBar";
import { useTheme } from "../../../styles/ThemeContext";
import { PrimaryButton } from "../../../styles/ui";

const ELECTIONS = [
    { id: 1, name: "General Election 2024" },
    { id: 2, name: "Local Election 2024" },
    { id: 3, name: "European Election 2024" },
    { id: 4, name: "Referendum 2024" },
    { id: 5, name: "Other" },
] // TODO: Replace with actual elections

function ElectionSelection({next, state, setState}: {next: () => void, state: any, setState: (state: any) => void}) {
    const { theme } = useTheme();
    return (
        <div style={{ ...getVoterPageContentWrapperStyle(theme), maxWidth: "100%", margin: "0 auto" }}>
            <div style={{...getCardStyle(theme), marginBottom: "1.75rem"}}>
                <ProgressBar step={1} theme={theme} />
            </div>
            <h2 style={getStepTitleStyle(theme)}>Select an Election</h2>
            <p style={getStepDescStyle(theme)}>Please select the election you wish to vote in.</p>
            {ELECTIONS.map(e => {
                const selected = state.election === e.id;
                return (
                    <label
                        key={e.id}
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
                            value={e.id}
                            checked={!!selected}
                            onChange={() => setState({...state, election: e.id})}
                            style={{ accentColor: theme.colors.button }}
                        />
                        <span style={{ fontSize: theme.fontSizes.base, color: theme.colors.text.primary }}>{e.name}</span>
                    </label>
                );
            })}
            <div style={{ marginTop: "1.75rem", display: "flex", justifyContent: "center" }}>
                <PrimaryButton onClick={next}>Next</PrimaryButton>
            </div>
        </div>
    )
} export default ElectionSelection;