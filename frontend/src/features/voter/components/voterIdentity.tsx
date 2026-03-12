// Voting Step: Voter Identity

import {
    PrimaryButton,
    getFirstSectionStyle,
    getPageTitleStyle,
    getCardStyle,
    getVoterPageContentWrapperStyle,
    getStepTitleStyle,
    getStepDescStyle,
    getStepFormInputStyle,
    getStepLabelStyle,
} from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";
import ProgressBar from "./progressBar";

function VoterIdentity({ next, state, setState, progressStep = 2, showProgressBar = true, usePageLayout = false }: { next: () => void; state: any; setState: (state: any) => void; progressStep?: number; showProgressBar?: boolean; usePageLayout?: boolean }) {
    const { theme } = useTheme();

    const fields = [
        { key: "name", label: "Full Name", placeholder: "e.g. Jane Smith" },
        { key: "addr1", label: "Address Line 1", placeholder: "House number and street" },
        { key: "addr2", label: "Address Line 2", placeholder: "Flat, apartment, etc." },
        { key: "city", label: "City / Town", placeholder: "e.g. London" },
        { key: "postcode", label: "Postcode", placeholder: "e.g. SW1A 1AA" },
    ];

    const formContent = (
        <>
            {!usePageLayout && (
                <>
                    {showProgressBar && (
                        <div style={{...getCardStyle(theme), marginBottom: "1.75rem"}}>
                            <ProgressBar step={progressStep} theme={theme} />
                        </div>
                    )}
                    <h1 style={getStepTitleStyle(theme)}>Confirm Your Identity</h1>
                    <p style={getStepDescStyle(theme)}>Please confirm your identity by providing the following information.</p>
                </>
            )}
            {usePageLayout && <p style={{ marginBottom: theme.spacing.md }}>Please confirm your identity by providing the following information.</p>}
            {fields.map(field => (
                <div key={field.key} style={{...getCardStyle(theme), marginBottom: "1rem"}}>
                    <label htmlFor={field.key} style={getStepLabelStyle(theme)}>
                        {field.label}
                    </label>
                    <input
                        type="text"
                        id={field.key}
                        name={field.key}
                        placeholder={field.placeholder}
                        value={state[field.key] || ""}
                        onChange={(e) => setState({...state, [field.key]: e.target.value})}
                        style={getStepFormInputStyle(theme)}
                    />
                </div>
            ))}
            <div style={{ marginTop: "1.75rem", display: "flex", justifyContent: usePageLayout ? "flex-start" : "center", gap: theme.spacing.md }}>
                <PrimaryButton onClick={next}>Next</PrimaryButton>
            </div>
        </>
    );

    if (usePageLayout) {
        return (
            <div className="voter-update-registration-page voter-page-content" style={getVoterPageContentWrapperStyle(theme)}>
                <header>
                    <h1 style={getPageTitleStyle(theme)}>Confirm your identity</h1>
                </header>
                <section style={getFirstSectionStyle(theme)}>
                    {formContent}
                </section>
            </div>
        );
    }

    return (
        <div style={{ ...getVoterPageContentWrapperStyle(theme), maxWidth: "100%", margin: "0 auto" }}>
            {formContent}
        </div>
    );
}

export default VoterIdentity;