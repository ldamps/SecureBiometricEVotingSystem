import { useRef } from "react";
import { getVoterPageContentWrapperStyle, getCardStyle, getStepTitleStyle, getStepLabelStyle, getStepFormInputStyle, getFirstSectionStyle, getPageTitleStyle, PrimaryButton, SecondaryButton } from "../../../styles/ui";
import ProgressBar from "./progressBar";
import { useTheme } from "../../../styles/ThemeContext";
import UK_COUNTIES from "../constants/ukCounties";

function CurrentAddress({
    next,
    back,
    state,
    setState,
    progressStep = 3,
    heading = "Registration: Current Address",
    showProgressBar = true,
    primaryButtonLabel = "Next",
    usePageLayout = false,
}: {
    next: () => void;
    back: () => void;
    state: any;
    setState: (state: any) => void;
    progressStep?: number;
    heading?: string;
    showProgressBar?: boolean;
    primaryButtonLabel?: string;
    usePageLayout?: boolean;
}) {
    const { theme } = useTheme();
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) setState({ ...state, proofOfAddressFile: file, proofOfAddressFileName: file.name });
    };

    const fields = [
        { key: "addressLine1", label: "Address Line 1", placeholder: "House number and street" },
        { key: "addressLine2", label: "Address Line 2", placeholder: "Flat, apartment, etc." },
        { key: "city", label: "City / Town", placeholder: "e.g. London" },
        { key: "postcode", label: "Postcode", placeholder: "e.g. SW1A 1AA" },
        { key: "county", label: "County", placeholder: "e.g. Surrey" },
        { key: "country", label: "Country", placeholder: "e.g. United Kingdom" },
    ];

    const formContent = (
        <>
            {!usePageLayout && (
                <div style={{ ...getCardStyle(theme), marginBottom: "1.75rem" }}>
                    {showProgressBar && <ProgressBar step={progressStep} theme={theme} />}
                    <h1 style={getStepTitleStyle(theme)}>{heading}</h1>
                </div>
            )}
            {fields.map(field => (
                <div key={field.key} style={{ ...getCardStyle(theme), marginBottom: "1rem" }}>
                    <label htmlFor={field.key} style={getStepLabelStyle(theme)}>
                        {field.label}
                    </label>
                    {field.key === "county" ? (
                        <select
                            id={field.key}
                            name={field.key}
                            value={state[field.key] || ""}
                            onChange={(e) => setState({ ...state, [field.key]: e.target.value })}
                            style={getStepFormInputStyle(theme)}
                        >
                            <option value="">Select a county</option>
                            {UK_COUNTIES.map((county) => (
                                <option key={county} value={county}>{county}</option>
                            ))}
                        </select>
                    ) : (
                        <input
                            type="text"
                            id={field.key}
                            name={field.key}
                            placeholder={field.placeholder}
                            value={state[field.key] || ""}
                            onChange={(e) => setState({ ...state, [field.key]: e.target.value })}
                            style={getStepFormInputStyle(theme)}
                        />
                    )}
                </div>
            ))}
            <div style={{ ...getCardStyle(theme), marginBottom: "1rem" }}>
                <label style={getStepLabelStyle(theme)}>Proof of address document</label>
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={handleFileChange}
                    style={{ display: "none" }}
                    aria-label="Upload proof of address"
                />
                <div style={{ display: "flex", alignItems: "center", gap: theme.spacing?.md ?? "1rem", flexWrap: "wrap" }}>
                    <SecondaryButton
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                    >
                        Upload file
                    </SecondaryButton>
                    {state.proofOfAddressFileName && (
                        <span style={{ fontSize: "0.875rem", color: theme.colors.text.secondary }}>
                            {state.proofOfAddressFileName}
                        </span>
                    )}
                </div>
            </div>
            <div style={{ marginTop: "1.75rem", display: "flex", justifyContent: usePageLayout ? "flex-start" : "center", gap: theme.spacing?.md ?? theme.spacing?.sm ?? "1rem" }}>
                <PrimaryButton onClick={back}>Back</PrimaryButton>
                <PrimaryButton onClick={next}>{primaryButtonLabel}</PrimaryButton>
            </div>
        </>
    );

    if (usePageLayout) {
        return (
            <div className="voter-update-registration-page voter-page-content" style={getVoterPageContentWrapperStyle(theme)}>
                <header>
                    <h1 style={getPageTitleStyle(theme)}>{heading}</h1>
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

export default CurrentAddress;