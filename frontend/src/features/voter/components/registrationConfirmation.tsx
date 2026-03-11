import { getCardStyle, getStepDescStyle, getStepTitleStyle, getVoterPageContentWrapperStyle } from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";
import ProgressBar from "./progressBar";
import PrimaryButton from "../../../components/PrimaryButton";
import { useNavigate } from "react-router-dom";

function RegistrationConfirmation({next, back, state, setState}: {next: () => void, back: () => void, state: any, setState: (state: any) => void}) {
    const { theme } = useTheme();
    const navigate = useNavigate();

    const handleFinish = () => {
        navigate("/voter/landing");
    }
    
    return (
        <div style={{ ...getVoterPageContentWrapperStyle(theme), maxWidth: "100%", margin: "0 auto" }}>
            <div style={{ ...getCardStyle(theme), marginBottom: "1.75rem" }}>
                <ProgressBar step={5} theme={theme} />
                <h1 style={getStepTitleStyle(theme)}>Registration: Finishing Up</h1>
            </div>
            <p style={getStepDescStyle(theme)}>
                Before you finish, please ensure all the information you have provided is correct and is your own information.
                <br />
                You may not register to vote on behalf of someone else.
                <br />
                <br />
                This information will be used to verify your identity during elections.
                <br />
                <br />
                You may update your registration details at any time on the platform by going to the manage your voting details page.
                <br />
                <br />
                Once you have finished this process, you will receive an email confirmation of your registration.
            </p>
            <label
                style={{
                    color: theme.colors.text.primary,
                    marginBottom: "1.75rem",
                    display: "flex",
                    alignItems: "center",
                    gap: theme.spacing.md,
                    cursor: "pointer",
                }}
            >
                <input type="checkbox" name="emailConfirmation" id="emailConfirmation" style={{ accentColor: theme.colors.button }} />
                <span style={{ fontSize: theme.fontSizes.base, color: theme.colors.text.primary }}>I confirm that the information I have provided is correct and is my own information.</span>
            </label>
            {/* Navigation */}
            <div style={{ marginTop: "1.75rem", display: "flex", justifyContent: "center", gap: theme.spacing.md }}>
                <PrimaryButton onClick={back}>Back</PrimaryButton>
                <PrimaryButton onClick={handleFinish}>Finish</PrimaryButton>
            </div>
        </div>
    )
}

export default RegistrationConfirmation;