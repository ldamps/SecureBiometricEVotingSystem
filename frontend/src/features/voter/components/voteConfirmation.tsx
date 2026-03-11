import ProgressBar from "./progressBar";
import { getVoterPageContentWrapperStyle, getCardStyle, getStepTitleStyle, getStepDescStyle } from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";
import PrimaryButton from "../../../components/PrimaryButton";
import { useNavigate } from "react-router-dom";

function VoteConfirmation({next, state, setState}: {next: () => void, state: any, setState: (state: any) => void}) {
    const { theme } = useTheme();
    const navigate = useNavigate();
    return (
        <div style={{ ...getVoterPageContentWrapperStyle(theme), maxWidth: "100%", margin: "0 auto" }}>
            <div style={{...getCardStyle(theme), marginBottom: "1.75rem"}}>
                <ProgressBar step={5} theme={theme} />
            </div>
            <h1 style={getStepTitleStyle(theme)}>Thank You for Voting!</h1>
            <p>
                Before you finish, please note you can only vote once. 
                <br />Once you have submitted your vote, you will not be able to change your vote.
            </p>
            <label
                style={{
                    ...getCardStyle(theme),
                    marginBottom: "1.75rem",
                    display: "flex",
                    alignItems: "center",
                    gap: theme.spacing.md,
                    cursor: "pointer",
                }}
            >
                <input
                    type="checkbox"
                    name="emailConfirmation"
                    id="emailConfirmation"
                    style={{ accentColor: theme.colors.button }}
                />
                <span style={{ fontSize: theme.fontSizes.base, color: theme.colors.text.primary }}>
                    I would like to receive an email confirmation
                </span>
            </label>
            <div style={{ display: "flex", justifyContent: "center" }}>
                <PrimaryButton onClick={() => navigate("/voter/landing")}>Finish</PrimaryButton>
            </div>
        </div>
    )
} export default VoteConfirmation;