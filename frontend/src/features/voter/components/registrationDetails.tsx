import { getVoterPageContentWrapperStyle, getCardStyle, getStepTitleStyle, getStepLabelStyle, getStepFormInputStyle, getFirstSectionStyle, getPageTitleStyle, PrimaryButton } from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";
import ProgressBar from "./progressBar";

const NATIONALITY_OPTIONS = [
    { key: "nationalityBritish", label: "British" },
    { key: "nationalityIrish", label: "Irish (including Northern Ireland)" },
    { key: "nationalityOtherCountry", label: "Citizen of a different country" },
] as const;

function RegistrationDetails({
    next,
    back,
    state,
    setState,
    progressStep = 2,
    heading = "Registration: Identity Details",
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
    const showOtherCountryInput = state.nationalityOtherCountry === true;
    const showPreviousNames = state.nameChanged === true;

    const baseFields = [
        { key: "firstName", label: "First Name", placeholder: "e.g. John" },
        { key: "lastName", label: "Last Name", placeholder: "e.g. Doe" },
        { key: "email", label: "Email", placeholder: "e.g. john.doe@example.com" },
        { key: "dateOfBirth", label: "Date of Birth", placeholder: "DD/MM/YYYY" },
        { key: "nationalInsuranceNumber", label: "National Insurance Number", placeholder: "e.g. 1234567890" },
        { key: "passportNumber", label: "Passport Number", placeholder: "e.g. 1234567890" },
    ];

    const toggleNationality = (key: string) => {
        const current = state[key];
        setState({ ...state, [key]: !current });
    };

    const checkboxStyle = (theme: any) => ({
        width: "1rem",
        height: "1rem",
        marginRight: theme.spacing.sm,
        accentColor: theme.colors?.primary ?? "#2563eb",
        cursor: "pointer",
    });

    const labelBlockStyle = (theme: any) => ({
        display: "flex",
        alignItems: "center",
        marginBottom: theme.spacing.sm,
        cursor: "pointer",
        fontSize: theme.fontSizes?.base ?? "1rem",
        color: theme.colors?.text?.primary ?? "#111",
    });

    const formContent = (
        <>
            {!usePageLayout && (
                <div style={{ ...getCardStyle(theme), marginBottom: "1.75rem" }}>
                    {showProgressBar && <ProgressBar step={progressStep} theme={theme} />}
                    <h1 style={getStepTitleStyle(theme)}>{heading}</h1>
                </div>
            )}

            {baseFields.map((field) => (
                <div key={field.key} style={{ ...getCardStyle(theme), marginBottom: "1rem" }}>
                    <label htmlFor={field.key} style={getStepLabelStyle(theme)}>
                        {field.label}
                    </label>
                    <input
                        type="text"
                        id={field.key}
                        name={field.key}
                        placeholder={field.placeholder}
                        value={state[field.key] || ""}
                        onChange={(e) => setState({ ...state, [field.key]: e.target.value })}
                        style={getStepFormInputStyle(theme)}
                    />
                </div>
            ))}

            {/* Nationality – multiple selection allowed */}
            <div style={{ ...getCardStyle(theme), marginBottom: "1rem" }}>
                <label style={{ ...getStepLabelStyle(theme), display: "block", marginBottom: "0.5rem" }}>
                    Nationality (select all that apply – include every country you are a citizen of)
                </label>
                {NATIONALITY_OPTIONS.map((opt) => (
                    <label key={opt.key} style={labelBlockStyle(theme)}>
                        <input
                            type="checkbox"
                            checked={!!state[opt.key]}
                            onChange={() => toggleNationality(opt.key)}
                            style={checkboxStyle(theme)}
                        />
                        {opt.label}
                    </label>
                ))}
                {showOtherCountryInput && (
                    <div style={{ marginTop: "0.75rem" }}>
                        <label htmlFor="otherCountries" style={getStepLabelStyle(theme)}>
                            Other country / countries (e.g. France, or France, Germany)
                        </label>
                        <input
                            type="text"
                            id="otherCountries"
                            name="otherCountries"
                            placeholder="e.g. France or France, Germany"
                            value={state.otherCountries || ""}
                            onChange={(e) => setState({ ...state, otherCountries: e.target.value })}
                            style={getStepFormInputStyle(theme)}
                        />
                    </div>
                )}
            </div>

            {/* Have you ever changed your name? */}
            <div style={{ ...getCardStyle(theme), marginBottom: "1rem" }}>
                <label style={{ ...getStepLabelStyle(theme), display: "block", marginBottom: "0.5rem" }}>
                    Have you ever changed your name?
                </label>
                <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
                    <label style={labelBlockStyle(theme)}>
                        <input
                            type="radio"
                            name="nameChanged"
                            checked={state.nameChanged === true}
                            onChange={() => setState({ ...state, nameChanged: true })}
                            style={{ marginRight: theme.spacing.sm, cursor: "pointer" }}
                        />
                        Yes
                    </label>
                    <label style={labelBlockStyle(theme)}>
                        <input
                            type="radio"
                            name="nameChanged"
                            checked={state.nameChanged === false || state.nameChanged == null}
                            onChange={() => setState({ ...state, nameChanged: false, previousFirstName: "", previousLastName: "" })}
                            style={{ marginRight: theme.spacing.sm, cursor: "pointer" }}
                        />
                        No
                    </label>
                </div>
                {showPreviousNames && (
                    <>
                        <div style={{ marginTop: "1rem" }}>
                            <label htmlFor="previousFirstName" style={getStepLabelStyle(theme)}>
                                Previous first name
                            </label>
                            <input
                                type="text"
                                id="previousFirstName"
                                name="previousFirstName"
                                placeholder="e.g. John"
                                value={state.previousFirstName || ""}
                                onChange={(e) => setState({ ...state, previousFirstName: e.target.value })}
                                style={getStepFormInputStyle(theme)}
                            />
                        </div>
                        <div style={{ marginTop: "0.75rem" }}>
                            <label htmlFor="previousLastName" style={getStepLabelStyle(theme)}>
                                Previous last name
                            </label>
                            <input
                                type="text"
                                id="previousLastName"
                                name="previousLastName"
                                placeholder="e.g. Doe"
                                value={state.previousLastName || ""}
                                onChange={(e) => setState({ ...state, previousLastName: e.target.value })}
                                style={getStepFormInputStyle(theme)}
                            />
                        </div>
                    </>
                )}
            </div>
            <div style={{ marginTop: "1.75rem", display: "flex", justifyContent: usePageLayout ? "flex-start" : "center", gap: theme.spacing.md }}>
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

export default RegistrationDetails;
