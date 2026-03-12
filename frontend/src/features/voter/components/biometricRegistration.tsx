import { PrimaryButton } from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";
import { getCardStyle, getStepTitleStyle } from "../../../styles/ui";
import ProgressBar from "./progressBar";

function BiometricRegistration({next, back, state, setState}: {next: () => void, back: () => void, state: any, setState: (state: any) => void}) {
    const { theme } = useTheme();
    return (
        <div>
            <div style={{ ...getCardStyle(theme), marginBottom: "1.75rem" }}>
                <ProgressBar step={4} theme={theme} />
                <h1 style={getStepTitleStyle(theme)}>Registration: Register Your Biometrics</h1>
            </div>
            {/* Navigation */}
            <div style={{ marginTop: "1.75rem", display: "flex", justifyContent: "center", gap: theme.spacing.md }}>
                <PrimaryButton onClick={back}>Back</PrimaryButton>
                <PrimaryButton onClick={next}>Next</PrimaryButton>
            </div>
        </div>
    )
}

export default BiometricRegistration;