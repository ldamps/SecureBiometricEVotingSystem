import { getVoterPageContentWrapperStyle, getCardStyle, getStepTitleStyle, getStepLabelStyle, getStepFormInputStyle } from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";
import ProgressBar from "./progressBar";
import { PrimaryButton } from "../../../styles/ui";
import UK_COUNTIES from "../constants/ukCounties";

const UK_REGIONS = [
    { key: "england",        label: "England" },
    { key: "scotland",       label: "Scotland" },
    { key: "wales",          label: "Wales" },
    { key: "northernIreland",label: "Northern Ireland" },
    { key: "overseas",       label: "British citizen living overseas" },
] as const;

/** Last UK address country — four nations only (matches radio region labels). */
const UK_NATION_OPTIONS = [
    { value: "England", label: "England" },
    { value: "Scotland", label: "Scotland" },
    { value: "Wales", label: "Wales" },
    { value: "Northern Ireland", label: "Northern Ireland" },
] as const;

const PREVIOUS_ADDRESS_FIELDS = [
    { key: "prevAddrLine1",    label: "Address Line 1",         placeholder: "House number and street", required: true  },
    { key: "prevAddrLine2",    label: "Address Line 2",         placeholder: "Flat, apartment, etc.",   required: false },
    { key: "prevAddrCity",     label: "City / Town",            placeholder: "e.g. London",             required: true  },
    { key: "prevAddrPostcode", label: "Postcode",               placeholder: "e.g. SW1A 1AA",           required: true  },
    { key: "prevAddrCounty",   label: "County",                 placeholder: "e.g. Surrey",             required: false },
    { key: "prevAddrCountry",  label: "Country",                placeholder: "",                        required: true },
] as const;

function LivingDetails({
    next,
    state,
    setState,
}: {
    next: () => void;
    state: any;
    setState: (state: any) => void;
}) {
    const { theme } = useTheme();

    const isOverseas = state.region === "overseas";

    const set = (patch: Record<string, any>) => setState({ ...state, ...patch });

    const labelBlockStyle = (t: any) => ({
        display: "flex",
        alignItems: "center",
        marginBottom: t.spacing.sm,
        cursor: "pointer",
        fontSize: t.fontSizes?.base ?? "1rem",
        color: t.colors?.text?.primary ?? "#111",
    });

    const requiredPrevFields = PREVIOUS_ADDRESS_FIELDS.filter((f) => f.required);
    const prevAddressComplete = requiredPrevFields.every((f) => state[f.key]?.trim());
    const canProceed = state.region && (!isOverseas || prevAddressComplete);

    return (
        <div style={{ ...getVoterPageContentWrapperStyle(theme), maxWidth: "100%", margin: "0 auto" }}>

            {/* Header */}
            <div style={{ ...getCardStyle(theme), marginBottom: "1.75rem" }}>
                <ProgressBar step={1} theme={theme} />
                <h1 style={getStepTitleStyle(theme)}>Registration: Country of Residence</h1>
            </div>

            {/* Region */}
            <div style={{ ...getCardStyle(theme), marginBottom: "1rem" }}>
                <label style={{ ...getStepLabelStyle(theme), display: "block", marginBottom: "0.5rem" }}>
                    Where do you currently live?
                </label>
                {UK_REGIONS.map((opt) => (
                    <label key={opt.key} style={labelBlockStyle(theme)}>
                        <input
                            type="radio"
                            name="region"
                            checked={state.region === opt.key}
                            onChange={() =>
                                set({
                                    region: opt.key,
                                    prevAddrLine1: "",
                                    prevAddrLine2: "",
                                    prevAddrCity: "",
                                    prevAddrPostcode: "",
                                    prevAddrCounty: "",
                                    prevAddrCountry: "",
                                })
                            }
                            style={{ marginRight: theme.spacing.sm, cursor: "pointer" }}
                        />
                        {opt.label}
                    </label>
                ))}
            </div>

            {/* Previous UK address — overseas only */}
            {isOverseas && (
                <div style={{ ...getCardStyle(theme), marginBottom: "1rem" }}>
                    <label style={{ ...getStepLabelStyle(theme), display: "block", marginBottom: "0.75rem" }}>
                        What was your last address in the UK?
                    </label>
                    {PREVIOUS_ADDRESS_FIELDS.map((f) => (
                        <div key={f.key} style={{ marginBottom: "0.75rem" }}>
                            <label htmlFor={f.key} style={getStepLabelStyle(theme)}>
                                {f.label}{f.required ? <span style={{ color: theme.colors.status.error }}> *</span> : " (optional)"}
                            </label>
                            {f.key === "prevAddrCounty" ? (
                                <select
                                    id={f.key}
                                    name={f.key}
                                    value={state[f.key] || ""}
                                    onChange={(e) => set({ [f.key]: e.target.value })}
                                    style={getStepFormInputStyle(theme)}
                                >
                                    <option value="">Select a county</option>
                                    {UK_COUNTIES.map((county) => (
                                        <option key={county} value={county}>{county}</option>
                                    ))}
                                </select>
                            ) : f.key === "prevAddrCountry" ? (
                                <select
                                    id={f.key}
                                    name={f.key}
                                    value={state[f.key] || ""}
                                    onChange={(e) => set({ [f.key]: e.target.value })}
                                    style={getStepFormInputStyle(theme)}
                                >
                                    <option value="">Select a country</option>
                                    {UK_NATION_OPTIONS.map((opt) => (
                                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                                    ))}
                                </select>
                            ) : (
                                <input
                                    type="text"
                                    id={f.key}
                                    name={f.key}
                                    placeholder={f.placeholder}
                                    value={state[f.key] || ""}
                                    onChange={(e) => set({ [f.key]: e.target.value })}
                                    style={getStepFormInputStyle(theme)}
                                />
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* Navigation */}
            <div style={{ marginTop: "1.75rem", display: "flex", justifyContent: "center", gap: theme.spacing.md }}>
                <PrimaryButton onClick={next} disabled={!canProceed}>Next</PrimaryButton>
            </div>
        </div>
    );
}

export default LivingDetails;