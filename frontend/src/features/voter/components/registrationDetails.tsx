import { useState as useLocalState } from "react";
import { getVoterPageContentWrapperStyle, getCardStyle, getStepTitleStyle, getStepLabelStyle, getStepFormInputStyle, getFirstSectionStyle, getPageTitleStyle, getErrorAlertStyle, PrimaryButton, SecondaryButton } from "../../../styles/ui";
import { useTheme } from "../../../styles/ThemeContext";
import ProgressBar from "./progressBar";
import COUNTRIES from "../constants/countries";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { loadStripe } from "@stripe/stripe-js";
import { VoterApiRepository } from "../repositories/voter-api.repository";
import { NationalityCategory } from "../model/voter.model";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL ?? "/api/v1";
const voterApi = new VoterApiRepository();

const NATIONALITY_OPTIONS = [
    { key: "nationalityBritish", label: "British" },
    { key: "nationalityIrish", label: "Irish (including Northern Ireland)" },
    { key: "nationalityOtherCountry", label: "Citizen of a different country" },
] as const;

/** Parse dd/mm/yyyy into a Date, or null if invalid. */
function parseDDMMYYYY(value: string): Date | null {
    const match = value.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    if (!match) return null;
    const [, dd, mm, yyyy] = match;
    const day = Number(dd);
    const month = Number(mm);
    const year = Number(yyyy);
    if (month < 1 || month > 12 || day < 1 || day > 31) return null;
    const date = new Date(year, month - 1, day);
    if (date.getFullYear() !== year || date.getMonth() !== month - 1 || date.getDate() !== day) return null;
    return date;
}

function getAge(dob: Date): number {
    const today = new Date();
    let age = today.getFullYear() - dob.getFullYear();
    const monthDiff = today.getMonth() - dob.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
        age--;
    }
    return age;
}

function getMinAge(region: string): number {
    if (region === "scotland" || region === "wales") return 14;
    return 16;
}

/** Returns the latest allowed date of birth for the given region (i.e. today minus minimum age). */
function getMaxDob(region: string): Date {
    const today = new Date();
    const minAge = getMinAge(region);
    return new Date(today.getFullYear() - minAge, today.getMonth(), today.getDate());
}

function getRegionLabel(region: string): string {
    const labels: Record<string, string> = {
        england: "England",
        scotland: "Scotland",
        wales: "Wales",
        northernIreland: "Northern Ireland",
        overseas: "the UK",
    };
    return labels[region] || "the UK";
}

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
    isUpdate = false,
    existingNI = "",
    existingPassportNumber = "",
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
    isUpdate?: boolean;
    existingNI?: string;
    existingPassportNumber?: string;
}) {
    const { theme } = useTheme();
    const showOtherCountryInput = state.nationalityOtherCountry === true;
    const showPreviousNames = state.nameChanged === true;

    const [validationErrors, setValidationErrors] = useLocalState<Record<string, string>>({});
    const [kycLoading, setKycLoading] = useLocalState(false);
    const [kycError, setKycError] = useLocalState<string | null>(null);
    const [kycMismatches, setKycMismatches] = useLocalState<string[]>([]);
    const [submitting, setSubmitting] = useLocalState(false);

    const idMethod: string = state.identificationMethod || "";
    const kycStatus: string = state.kycStatus || "";

    // In update mode, KYC is only required when adding a new NI or changing passport
    const isAddingNI = isUpdate && !existingNI && idMethod === "ni" && !!state.nationalInsuranceNumber?.trim();
    const isChangingPassport = isUpdate && idMethod === "passport" && !!state.passportNumber?.trim() && state.passportNumber.trim() !== existingPassportNumber;
    const updateRequiresKyc = isAddingNI || isChangingPassport;
    const niIsReadOnly = isUpdate && !!existingNI;

    /** Compare form inputs against Stripe-extracted data and return mismatches. */
    const compareWithExtracted = (extracted: any, currentState: any): string[] => {
        const issues: string[] = [];
        const norm = (s: string) => (s || "").trim().toLowerCase();

        if (extracted.first_name && norm(extracted.first_name) !== norm(currentState.firstName)) {
            issues.push(`First name: you entered "${currentState.firstName}", document shows "${extracted.first_name}"`);
        }
        if (extracted.last_name && norm(extracted.last_name) !== norm(currentState.lastName)) {
            issues.push(`Last name: you entered "${currentState.lastName}", document shows "${extracted.last_name}"`);
        }
        if (extracted.date_of_birth && norm(extracted.date_of_birth) !== norm(currentState.dateOfBirth)) {
            issues.push(`Date of birth: you entered "${currentState.dateOfBirth}", document shows "${extracted.date_of_birth}"`);
        }
        if (currentState.identificationMethod === "passport" && extracted.document_number) {
            if (norm(extracted.document_number) !== norm(currentState.passportNumber)) {
                issues.push(`Passport number: you entered "${currentState.passportNumber}", document shows "${extracted.document_number}"`);
            }
        }
        return issues;
    };

    const startKycVerification = async () => {
        setKycLoading(true);
        setKycError(null);
        setKycMismatches([]);
        try {
            const res = await fetch(`${API_BASE_URL}/kyc/session`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    email: state.email || "",
                    allowed_document_types: idMethod === "passport"
                        ? ["passport", "driving_license"]
                        : ["passport", "driving_license", "id_card"],
                }),
            });
            if (!res.ok) throw new Error("Failed to create verification session");
            const data = await res.json();
            const sid = data.session_id;
            setState({ ...state, kycSessionId: sid });

            const stripe = await loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY || "");
            if (!stripe) throw new Error("Failed to load Stripe");

            const result = await stripe.verifyIdentity(data.client_secret);
            if (result.error) {
                setKycError(result.error.message || "Verification failed");
                setKycLoading(false);
                return;
            }

            // Poll for result, then fetch verified data on success
            const poll = async () => {
                const statusRes = await fetch(`${API_BASE_URL}/kyc/session/${sid}/status`);
                if (!statusRes.ok) throw new Error("Failed to check status");
                const statusData = await statusRes.json();
                const newStatus = statusData.status || "";
                setState((prev: any) => ({ ...prev, kycSessionId: sid, kycStatus: newStatus }));

                if (newStatus === "processing") {
                    setTimeout(poll, 3000);
                } else if (newStatus === "verified") {
                    // Fetch extracted data and compare against form.
                    // In Stripe test mode the extracted data is always dummy
                    // ("Jenny Rosen"), so skip the comparison to avoid false warnings.
                    const isTestMode = (process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY || "").startsWith("pk_test_");
                    if (!isTestMode) {
                        try {
                            const verifiedRes = await fetch(`${API_BASE_URL}/kyc/session/${sid}/verified-data`);
                            if (verifiedRes.ok) {
                                const verifiedData = await verifiedRes.json();
                                if (verifiedData.verified && verifiedData.extracted_data) {
                                    const mismatches = compareWithExtracted(verifiedData.extracted_data, state);
                                    setKycMismatches(mismatches);
                                }
                            }
                        } catch {
                            // Non-fatal — verification passed, comparison is best-effort
                        }
                    }
                }
            };
            await poll();
        } catch (err: any) {
            setKycError(err.message || "An error occurred");
        } finally {
            setKycLoading(false);
        }
    };

    const commonFields = [
        { key: "firstName", label: "First Name(s)", placeholder: "e.g. John", type: "text", required: !isUpdate },
        { key: "lastName", label: "Last Name", placeholder: "e.g. Doe", type: "text", required: !isUpdate },
        { key: "email", label: "Email", placeholder: "e.g. john.doe@example.com", type: "text", required: !isUpdate },
        ...(!isUpdate ? [{ key: "dateOfBirth", label: "Date of Birth", placeholder: "", type: "date", required: true }] : []),
    ];

    const niFields = [
        { key: "nationalInsuranceNumber", label: "National Insurance Number", placeholder: "e.g. QQ 12 34 56 C", type: "text" },
    ];

    const passportFields = [
        { key: "passportNumber", label: "Passport Number", placeholder: "e.g. 123456789", type: "text" },
        { key: "passportCountry", label: "Passport Country", placeholder: "", type: "select" },
        { key: "passportExpiryDate", label: "Passport Expiry Date", placeholder: "", type: "date" },
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

            {validationErrors.submit && (
                <div style={{
                    ...getCardStyle(theme),
                    ...getErrorAlertStyle(theme),
                    marginBottom: "1rem",
                }}>
                    <p style={{ color: theme.colors.status.error, fontSize: "0.9rem", fontWeight: 600, margin: 0 }}>
                        {validationErrors.submit}
                    </p>
                </div>
            )}

            {/* Common fields (name, email, DOB) */}
            {commonFields.map((field) => (
                <div key={field.key} style={{ ...getCardStyle(theme), marginBottom: "1rem" }}>
                    <label htmlFor={field.key} style={getStepLabelStyle(theme)}>
                        {field.label}{field.required && <span style={{ color: theme.colors.status.error }}> *</span>}
                    </label>
                    {validationErrors[field.key] && (
                        <p style={{ color: theme.colors.status.error, fontSize: "0.875rem", marginTop: "0.25rem", marginBottom: "0.25rem" }}>
                            {validationErrors[field.key]}
                        </p>
                    )}
                    {field.type === "date" ? (
                        <div style={{ display: "block", width: "100%" }}>
                            <DatePicker
                                id={field.key}
                                dateFormat="dd/MM/yyyy"
                                placeholderText="dd/mm/yyyy"
                                selected={parseDDMMYYYY(state[field.key] || "")}
                                onChange={(date: Date | null) => {
                                    const formatted = date
                                        ? `${String(date.getDate()).padStart(2, "0")}/${String(date.getMonth() + 1).padStart(2, "0")}/${date.getFullYear()}`
                                        : "";
                                    setState({ ...state, [field.key]: formatted });
                                    if (field.key === "dateOfBirth") setValidationErrors((prev) => ({ ...prev, dateOfBirth: "" }));
                                }}
                                maxDate={field.key === "dateOfBirth" ? getMaxDob(state.region) : undefined}
                                showYearDropdown
                                showMonthDropdown
                                dropdownMode="select"
                                popperPlacement="bottom-start"
                                customInput={<input style={{ ...getStepFormInputStyle(theme), width: "100%" }} />}
                            />
                        </div>
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
                    {/* DOB age errors are handled by validationErrors */}
                </div>
            ))}

            {/* Identity verification method + conditional fields in one card */}
            <div style={{ ...getCardStyle(theme), marginBottom: "1rem" }}>
                <label style={{ ...getStepLabelStyle(theme), display: "block", marginBottom: "0.5rem" }}>
                    How would you like to verify your identity?{!isUpdate && <span style={{ color: theme.colors.status.error }}> *</span>}
                </label>
                {validationErrors.identificationMethod && (
                    <p style={{ color: theme.colors.status.error, fontSize: "0.875rem", marginTop: "0.25rem", marginBottom: "0.25rem" }}>
                        {validationErrors.identificationMethod}
                    </p>
                )}
                <label style={labelBlockStyle(theme)}>
                    <input
                        type="radio"
                        name="identificationMethod"
                        checked={idMethod === "ni"}
                        onChange={() => setState({
                            ...state,
                            identificationMethod: "ni",
                            passportNumber: "",
                            passportCountry: "",
                            passportExpiryDate: "",
                        })}
                        style={{ marginRight: theme.spacing.sm, cursor: "pointer" }}
                    />
                    National Insurance Number
                </label>
                <label style={labelBlockStyle(theme)}>
                    <input
                        type="radio"
                        name="identificationMethod"
                        checked={idMethod === "passport"}
                        onChange={() => setState({
                            ...state,
                            identificationMethod: "passport",
                            nationalInsuranceNumber: "",
                        })}
                        style={{ marginRight: theme.spacing.sm, cursor: "pointer" }}
                    />
                    Passport
                </label>

                {/* Conditional fields rendered inside the same card */}
                {idMethod && (
                    <div style={{ marginTop: "0.75rem" }}>
                        {(idMethod === "ni" ? niFields : passportFields).map((field) => {
                            const fieldIsNIReadOnly = niIsReadOnly && field.key === "nationalInsuranceNumber";
                            return (
                            <div key={field.key} style={{ marginBottom: "0.75rem" }}>
                                <label htmlFor={field.key} style={getStepLabelStyle(theme)}>
                                    {field.label}{!isUpdate && <span style={{ color: theme.colors.status.error }}> *</span>}
                                </label>
                                {fieldIsNIReadOnly && (
                                    <p style={{ fontSize: "0.85rem", color: theme.colors.text.secondary, marginTop: "0.25rem", marginBottom: "0.25rem" }}>
                                        Your National Insurance Number cannot be changed once registered.
                                    </p>
                                )}
                                {validationErrors[field.key] && (
                                    <p style={{ color: theme.colors.status.error, fontSize: "0.875rem", marginTop: "0.25rem", marginBottom: "0.25rem" }}>
                                        {validationErrors[field.key]}
                                    </p>
                                )}
                                {field.type === "select" ? (
                                    <select
                                        id={field.key}
                                        name={field.key}
                                        value={state[field.key] || ""}
                                        onChange={(e) => setState({ ...state, [field.key]: e.target.value })}
                                        style={getStepFormInputStyle(theme)}
                                    >
                                        <option value="">Select a country</option>
                                        {COUNTRIES.map((c) => (
                                            <option key={c} value={c}>{c}</option>
                                        ))}
                                    </select>
                                ) : field.type === "date" ? (
                                    <div style={{ display: "block", width: "100%" }}>
                                        <DatePicker
                                            id={field.key}
                                            dateFormat="dd/MM/yyyy"
                                            placeholderText="dd/mm/yyyy"
                                            selected={parseDDMMYYYY(state[field.key] || "")}
                                            onChange={(date: Date | null) => {
                                                const formatted = date
                                                    ? `${String(date.getDate()).padStart(2, "0")}/${String(date.getMonth() + 1).padStart(2, "0")}/${date.getFullYear()}`
                                                    : "";
                                                setState({ ...state, [field.key]: formatted });
                                            }}
                                            showYearDropdown
                                            showMonthDropdown
                                            dropdownMode="select"
                                            popperPlacement="bottom-start"
                                            customInput={<input style={{ ...getStepFormInputStyle(theme), width: "100%" }} />}
                                        />
                                    </div>
                                ) : (
                                    <input
                                        type="text"
                                        id={field.key}
                                        name={field.key}
                                        placeholder={field.placeholder}
                                        value={state[field.key] || ""}
                                        onChange={(e) => {
                                            if (!fieldIsNIReadOnly) setState({ ...state, [field.key]: e.target.value });
                                        }}
                                        readOnly={fieldIsNIReadOnly}
                                        style={{
                                            ...getStepFormInputStyle(theme),
                                            ...(fieldIsNIReadOnly ? { backgroundColor: "#f3f4f6", cursor: "not-allowed" } : {}),
                                        }}
                                    />
                                )}
                            </div>
                            );
                        })}

                        {/* Stripe Identity verification – always for registration, only when needed for update */}
                        {(!isUpdate || updateRequiresKyc) && (
                        <div style={{ marginTop: "1rem", paddingTop: "0.75rem", borderTop: `1px solid ${theme.colors.border}` }}>
                            <p style={{ ...getStepLabelStyle(theme), marginBottom: "0.5rem" }}>
                                Verify your identity{!isUpdate && <span style={{ color: theme.colors.status.error }}> *</span>}
                            </p>
                            {isUpdate && (
                                <p style={{ fontSize: "0.85rem", color: theme.colors.text.secondary, marginBottom: "0.5rem" }}>
                                    {isAddingNI
                                        ? "Adding a National Insurance Number requires identity verification."
                                        : "Changing your passport details requires identity verification."}
                                </p>
                            )}
                            {validationErrors.kyc && (
                                <p style={{ color: theme.colors.status.error, fontSize: "0.875rem", marginTop: "0.25rem", marginBottom: "0.25rem" }}>
                                    {validationErrors.kyc}
                                </p>
                            )}
                            <p style={{ fontSize: "0.85rem", color: theme.colors.text.secondary, marginBottom: "0.75rem" }}>
                                {idMethod === "passport"
                                    ? "You will be asked to provide a photo of your passport or driving licence and take a selfie."
                                    : "You will be asked to provide any valid UK photo ID (passport, driving licence, biometric residence permit, or national ID card) and take a selfie."}
                            </p>
                            {/* TODO: Verify NI number against HMRC/DWP records once API access is available */}

                            {kycStatus === "verified" ? (
                                <>
                                    <p style={{ color: "#38a169", fontWeight: 600, fontSize: "0.9rem" }}>
                                        Identity verified successfully.
                                    </p>
                                    {kycMismatches.length > 0 && (
                                        <div style={{
                                            marginTop: "0.75rem",
                                            padding: "0.75rem",
                                            backgroundColor: "#fffbeb",
                                            border: "1px solid #f59e0b",
                                            borderRadius: "6px",
                                        }}>
                                            <p style={{ color: "#b45309", fontWeight: 600, fontSize: "0.85rem", marginBottom: "0.4rem" }}>
                                                Some details do not match your document:
                                            </p>
                                            <ul style={{ margin: 0, paddingLeft: "1.25rem", fontSize: "0.85rem", color: "#92400e" }}>
                                                {kycMismatches.map((m, i) => (
                                                    <li key={i} style={{ marginBottom: "0.25rem" }}>{m}</li>
                                                ))}
                                            </ul>
                                            <p style={{ color: "#92400e", fontSize: "0.8rem", marginTop: "0.5rem" }}>
                                                Please correct the details above to match your document before continuing.
                                            </p>
                                        </div>
                                    )}
                                    {kycMismatches.length === 0 && (
                                        <p style={{ color: "#38a169", fontSize: "0.85rem", marginTop: "0.25rem" }}>
                                            All details match your identity document.
                                        </p>
                                    )}
                                </>
                            ) : (
                                <SecondaryButton onClick={startKycVerification} disabled={kycLoading}>
                                    {kycLoading ? "Verifying..." : kycStatus === "requires_input" || kycStatus === "canceled" ? "Retry Verification" : "Verify Identity"}
                                </SecondaryButton>
                            )}

                            {kycStatus === "processing" && (
                                <p style={{ fontSize: "0.85rem", color: theme.colors.text.secondary, marginTop: "0.5rem" }}>
                                    Verification is being processed...
                                </p>
                            )}

                            {kycError && (
                                <p style={{ color: "#dc2626", fontSize: "0.85rem", marginTop: "0.5rem" }}>
                                    {kycError}
                                </p>
                            )}
                        </div>
                        )}
                    </div>
                )}
            </div>

            {/* Nationality – multiple selection allowed */}
            <div style={{ ...getCardStyle(theme), marginBottom: "1rem" }}>
                <label style={{ ...getStepLabelStyle(theme), display: "block", marginBottom: "0.5rem" }}>
                    Nationality (select all that apply – include every country you are a citizen of){!isUpdate && <span style={{ color: theme.colors.status.error }}> *</span>}
                </label>
                {validationErrors.nationality && (
                    <p style={{ color: theme.colors.status.error, fontSize: "0.875rem", marginTop: "0.25rem", marginBottom: "0.25rem" }}>
                        {validationErrors.nationality}
                    </p>
                )}
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
                            Which countries are you a citizen of?{!isUpdate && <span style={{ color: theme.colors.status.error }}> *</span>}
                        </label>
                        {validationErrors.otherCountries && (
                            <p style={{ color: theme.colors.status.error, fontSize: "0.875rem", marginTop: "0.25rem", marginBottom: "0.25rem" }}>
                                {validationErrors.otherCountries}
                            </p>
                        )}
                        <select
                            id="otherCountries"
                            name="otherCountries"
                            multiple
                            value={state.otherCountries || []}
                            onChange={(e) => {
                                const selected = Array.from(e.target.selectedOptions, (o) => o.value);
                                setState({ ...state, otherCountries: selected });
                            }}
                            style={{ ...getStepFormInputStyle(theme), minHeight: "8rem" }}
                        >
                            {COUNTRIES.map((c) => (
                                <option key={c} value={c}>{c}</option>
                            ))}
                        </select>
                        {(state.otherCountries as string[] || []).length > 0 && (
                            <p style={{ fontSize: "0.85rem", color: theme.colors.text.secondary, marginTop: "0.5rem" }}>
                                Selected: {(state.otherCountries as string[]).join(", ")}
                            </p>
                        )}
                    </div>
                )}
            </div>

            {/* Have you ever changed your name? */}
            <div style={{ ...getCardStyle(theme), marginBottom: "1rem" }}>
                <label style={{ ...getStepLabelStyle(theme), display: "block", marginBottom: "0.5rem" }}>
                    Have you ever changed your name?{!isUpdate && <span style={{ color: theme.colors.status.error }}> *</span>}
                </label>
                {validationErrors.nameChanged && (
                    <p style={{ color: theme.colors.status.error, fontSize: "0.875rem", marginTop: "0.25rem", marginBottom: "0.25rem" }}>
                        {validationErrors.nameChanged}
                    </p>
                )}
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
                            checked={state.nameChanged === false}
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
                                Previous first name{!isUpdate && <span style={{ color: theme.colors.status.error }}> *</span>}
                            </label>
                            {validationErrors.previousFirstName && (
                                <p style={{ color: theme.colors.status.error, fontSize: "0.875rem", marginTop: "0.25rem", marginBottom: "0.25rem" }}>
                                    {validationErrors.previousFirstName}
                                </p>
                            )}
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
                                Previous last name{!isUpdate && <span style={{ color: theme.colors.status.error }}> *</span>}
                            </label>
                            {validationErrors.previousLastName && (
                                <p style={{ color: theme.colors.status.error, fontSize: "0.875rem", marginTop: "0.25rem", marginBottom: "0.25rem" }}>
                                    {validationErrors.previousLastName}
                                </p>
                            )}
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
                <PrimaryButton disabled={submitting} onClick={async () => {
                    if (submitting) return;
                    const errors: Record<string, string> = {};

                    if (!isUpdate) {
                        // Required common fields (registration only)
                        if (!state.firstName?.trim()) errors.firstName = "First name is required.";
                        if (!state.lastName?.trim()) errors.lastName = "Surname is required.";
                        if (!state.email?.trim()) errors.email = "Email is required.";
                        if (!state.dateOfBirth?.trim()) errors.dateOfBirth = "Date of birth is required.";
                    }

                    // Date of birth validation (not shown in update mode)
                    if (!isUpdate) {
                        const dob = parseDDMMYYYY(state.dateOfBirth || "");
                        if (state.dateOfBirth && !dob) {
                            errors.dateOfBirth = "Please enter a valid date in dd/mm/yyyy format.";
                        }
                        if (dob && state.region) {
                            const minAge = getMinAge(state.region);
                            const age = getAge(dob);
                            if (age < minAge) {
                                errors.dateOfBirth = `You must be at least ${minAge} years old to register to vote in ${getRegionLabel(state.region)}.`;
                            }
                        }
                    }

                    if (!isUpdate) {
                        // Identification method required (registration only)
                        if (!idMethod) {
                            errors.identificationMethod = "Please select an identification method.";
                        } else if (idMethod === "ni") {
                            if (!state.nationalInsuranceNumber?.trim()) errors.nationalInsuranceNumber = "National Insurance Number is required.";
                        } else if (idMethod === "passport") {
                            if (!state.passportNumber?.trim()) errors.passportNumber = "Passport number is required.";
                            if (!state.passportCountry) errors.passportCountry = "Passport country is required.";
                            if (!state.passportExpiryDate?.trim()) errors.passportExpiryDate = "Passport expiry date is required.";
                        }

                        // Identity verification required (registration only)
                        if (kycStatus !== "verified") {
                            errors.kyc = "Please verify your identity before continuing.";
                        }

                        // Name change question required (registration only)
                        if (state.nameChanged == null) {
                            errors.nameChanged = "Please indicate whether you have ever changed your name.";
                        } else if (state.nameChanged === true) {
                            if (!state.previousFirstName?.trim()) errors.previousFirstName = "Previous first name is required.";
                            if (!state.previousLastName?.trim()) errors.previousLastName = "Previous last name is required.";
                        }

                        // Nationality required (registration only)
                        const hasNationality = state.nationalityBritish || state.nationalityIrish || state.nationalityOtherCountry;
                        if (!hasNationality) {
                            errors.nationality = "Please select at least one nationality.";
                        }
                        if (state.nationalityOtherCountry && (!state.otherCountries || (state.otherCountries as string[]).length === 0)) {
                            errors.otherCountries = "Please select at least one country.";
                        }
                    } else {
                        // Update mode: KYC required only if adding NI or changing passport
                        if (updateRequiresKyc && kycStatus !== "verified") {
                            errors.kyc = isAddingNI
                                ? "Please verify your identity before adding a National Insurance Number."
                                : "Please verify your identity before changing your passport details.";
                        }
                    }

                    setValidationErrors(errors);
                    if (Object.keys(errors).length > 0) return;

                    // Create the voter if not already created (needed for biometric enrollment in step 4)
                    // In update mode, voter already exists — skip creation
                    if (!isUpdate && !state.voterId) {
                        setSubmitting(true);
                        try {
                            const passports = [];
                            if (idMethod === "passport" && state.passportNumber?.trim()) {
                                passports.push({
                                    id: "",
                                    passport_number: state.passportNumber.trim(),
                                    issuing_country: state.passportCountry || "GB",
                                    expiry_date: state.passportExpiryDate || "",
                                    is_primary: true,
                                });
                            }

                            const renewBy = new Date();
                            renewBy.setFullYear(renewBy.getFullYear() + 1);

                            let natCat = NationalityCategory.OTHER;
                            if (state.nationalityBritish) natCat = NationalityCategory.BRITISH_CITIZEN;
                            else if (state.nationalityIrish) natCat = NationalityCategory.IRISH_CITIZEN;

                            const result = await voterApi.registerVoter({
                                kyc_session_id: state.kycSessionId,
                                first_name: state.firstName,
                                surname: state.lastName,
                                previous_first_name: state.nameChanged ? state.previousFirstName : undefined,
                                previous_surname: state.nameChanged ? state.previousLastName : undefined,
                                date_of_birth: state.dateOfBirth,
                                email: state.email,
                                national_insurance_number:
                                    idMethod === "ni" ? state.nationalInsuranceNumber : undefined,
                                passports,
                                nationality_category: natCat,
                                renew_by: renewBy.toISOString(),
                            });

                            setState((prev: any) => ({ ...prev, voterId: result.id }));
                        } catch (err: any) {
                            setValidationErrors({ submit: err.message || "Failed to create voter record. Please try again." });
                            setSubmitting(false);
                            return;
                        }
                    }

                    next();
                }}>{primaryButtonLabel}</PrimaryButton>
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
