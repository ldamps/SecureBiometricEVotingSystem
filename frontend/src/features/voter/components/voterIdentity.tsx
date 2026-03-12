// Voting Step: Voter Identity

import { PrimaryButton } from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";
import { getCardStyle, getVoterPageContentWrapperStyle, getStepTitleStyle, getStepDescStyle, getStepFormInputStyle, getStepLabelStyle } from "../../../styles/ui";
import ProgressBar from "./progressBar";

function VoterIdentity({next, state, setState}: {next: () => void, state: any, setState: (state: any) => void}) {
    const { theme } = useTheme();

    const fields = [
        { key: "name", label: "Full Name", placeholder: "e.g. Jane Smith" },
        { key: "addr1", label: "Address Line 1", placeholder: "House number and street" },
        { key: "addr2", label: "Address Line 2", placeholder: "Flat, apartment, etc." },
        { key: "city", label: "City / Town", placeholder: "e.g. London" },
        { key: "postcode", label: "Postcode", placeholder: "e.g. SW1A 1AA" },
    ];

    return (
        <div style={{ ...getVoterPageContentWrapperStyle(theme), maxWidth: "100%", margin: "0 auto" }}>
            <div style={{...getCardStyle(theme), marginBottom: "1.75rem"}}>
                <ProgressBar step={2} theme={theme} />
            </div>
            <h1 style={getStepTitleStyle(theme)}>Confirm Your Identity</h1>
            <p style={getStepDescStyle(theme)}>Please confirm your identity by providing the following information.</p>
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
            <div style={{ marginTop: "1.75rem", display: "flex", justifyContent: "center" }}>
                <PrimaryButton onClick={next}>Next</PrimaryButton>
            </div>
        </div>
    )
}

export default VoterIdentity;