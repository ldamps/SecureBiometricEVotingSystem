// Voting Step: Biometric Verification

import ProgressBar from "./progressBar";
import { getVoterPageContentWrapperStyle, getCardStyle, getStepTitleStyle, getStepDescStyle } from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";
import { PrimaryButton } from "../../../styles/ui";

function BiometricVerification({next, state, setState}: {next: () => void, state: any, setState: (state: any) => void}) {
    const { theme } = useTheme();
    return (
        <div style={{ ...getVoterPageContentWrapperStyle(theme), maxWidth: "100%", margin: "0 auto" }}>
            <div style={{...getCardStyle(theme), marginBottom: "1.75rem"}}>
                <ProgressBar step={3} theme={theme} />
            </div>
            <h1 style={getStepTitleStyle(theme)}>Biometric Verification</h1>
            <p style={getStepDescStyle(theme)}>Please verify your identity by providing your biometric information.</p>
            <div style={{ marginTop: "1.75rem", display: "flex", justifyContent: "center" }}>
                <PrimaryButton onClick={next}>Next</PrimaryButton>
            </div>
        </div>
    )
} export default BiometricVerification;