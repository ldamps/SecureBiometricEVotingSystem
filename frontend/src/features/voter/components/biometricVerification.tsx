// Voting Step: Biometric Verification

import ProgressBar from "./progressBar";
import { getVoterPageContentWrapperStyle, getCardStyle, getStepTitleStyle, getStepDescStyle, getFirstSectionStyle, getPageTitleStyle, PrimaryButton } from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";

function BiometricVerification({ next, state, setState, progressStep = 3, showProgressBar = true, usePageLayout = false }: { next: () => void; state: any; setState: (state: any) => void; progressStep?: number; showProgressBar?: boolean; usePageLayout?: boolean }) {
    const { theme } = useTheme();

    const content = (
        <>
            {!usePageLayout && (
                <>
                    {showProgressBar && (
                        <div style={{...getCardStyle(theme), marginBottom: "1.75rem"}}>
                            <ProgressBar step={progressStep} theme={theme} />
                        </div>
                    )}
                    <h1 style={getStepTitleStyle(theme)}>Biometric Verification</h1>
                    <p style={getStepDescStyle(theme)}>Please verify your identity by providing your biometric information.</p>
                </>
            )}
            {usePageLayout && <p style={{ marginBottom: theme.spacing.md }}>Please verify your identity by providing your biometric information.</p>}
            <div style={{ marginTop: usePageLayout ? 0 : "1.75rem", display: "flex", justifyContent: usePageLayout ? "flex-start" : "center", gap: theme.spacing.md }}>
                <PrimaryButton onClick={next}>Next</PrimaryButton>
            </div>
        </>
    );

    if (usePageLayout) {
        return (
            <div className="voter-update-registration-page voter-page-content" style={getVoterPageContentWrapperStyle(theme)}>
                <header>
                    <h1 style={getPageTitleStyle(theme)}>Biometric verification</h1>
                </header>
                <section style={getFirstSectionStyle(theme)}>
                    {content}
                </section>
            </div>
        );
    }

    return (
        <div style={{ ...getVoterPageContentWrapperStyle(theme), maxWidth: "100%", margin: "0 auto" }}>
            {content}
        </div>
    );
}

export default BiometricVerification;