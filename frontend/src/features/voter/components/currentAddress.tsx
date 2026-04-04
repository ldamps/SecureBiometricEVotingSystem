import { useRef, useState } from "react";
import { getVoterPageContentWrapperStyle, getCardStyle, getStepTitleStyle, getStepLabelStyle, getStepFormInputStyle, getFirstSectionStyle, getPageTitleStyle, PrimaryButton, SecondaryButton } from "../../../styles/ui";
import ProgressBar from "./progressBar";
import { useTheme } from "../../../styles/ThemeContext";
import UK_COUNTIES from "../constants/ukCounties";
import COUNTRIES from "../constants/countries";
import { VoterApiRepository } from "../repositories/voter-api.repository";
import { AddressType } from "../model/voter.model";

const voterApi = new VoterApiRepository();

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

    const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
    const [verifying, setVerifying] = useState(false);
    const [addressVerified, setAddressVerified] = useState(state.addressVerified || false);
    const isUkAddress = (state.country || "").toLowerCase().includes("united kingdom") || (state.country || "").toLowerCase().includes("uk");

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) setState({ ...state, proofOfAddressFile: file, proofOfAddressFileName: file.name });
    };

    const fields = [
        { key: "addressLine1", label: "Address Line 1", placeholder: "House number and street", required: true },
        { key: "addressLine2", label: "Address Line 2", placeholder: "Flat, apartment, etc.", required: false },
        { key: "city", label: "City / Town", placeholder: "e.g. London", required: true },
        { key: "postcode", label: "Postcode", placeholder: "e.g. SW1A 1AA", required: isUkAddress },
        { key: "county", label: "County", placeholder: "e.g. Surrey", required: false },
        { key: "country", label: "Country", placeholder: "", required: true },
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
                        {field.label}{field.required ? <span style={{ color: theme.colors.status.error }}> *</span> : ""}
                    </label>
                    {validationErrors[field.key] && (
                        <p style={{ color: theme.colors.status.error, fontSize: "0.875rem", marginTop: "0.25rem", marginBottom: "0.25rem" }}>
                            {validationErrors[field.key]}
                        </p>
                    )}
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
                    ) : field.key === "country" ? (
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
            {/* Proof of address upload */}
            <div style={{ ...getCardStyle(theme), marginBottom: "1rem" }}>
                <p style={{ ...getStepLabelStyle(theme), marginBottom: "0.5rem" }}>
                    Proof of address<span style={{ color: theme.colors.status.error }}> *</span>
                </p>
                <p style={{ fontSize: "0.85rem", color: theme.colors.text.secondary, marginBottom: "0.75rem" }}>
                    Please upload a proof of address (e.g. utility bill, bank statement, or council tax bill dated within the last 3 months).
                </p>
                {validationErrors.proofOfAddress && (
                    <p style={{ color: theme.colors.status.error, fontSize: "0.875rem", marginTop: "0.25rem", marginBottom: "0.25rem" }}>
                        {validationErrors.proofOfAddress}
                    </p>
                )}

                <input
                    type="file"
                    ref={fileInputRef}
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={handleFileChange}
                    style={{ display: "none" }}
                />
                <SecondaryButton onClick={() => fileInputRef.current?.click()}>
                    {state.proofOfAddressFileName ? "Change File" : "Upload Proof of Address"}
                </SecondaryButton>
                {state.proofOfAddressFileName && (
                    <p style={{ color: theme.colors.status.success, fontSize: "0.85rem", marginTop: "0.5rem", fontWeight: 600 }}>
                        Uploaded: {state.proofOfAddressFileName}
                    </p>
                )}
            </div>

            <div style={{ marginTop: "1.75rem", display: "flex", justifyContent: usePageLayout ? "flex-start" : "center", gap: theme.spacing?.md ?? theme.spacing?.sm ?? "1rem" }}>
                <PrimaryButton onClick={back}>Back</PrimaryButton>
                <PrimaryButton
                    disabled={verifying}
                    onClick={async () => {
                        const errors: Record<string, string> = {};

                        if (!state.addressLine1?.trim()) errors.addressLine1 = "Address line 1 is required.";
                        if (!state.city?.trim()) errors.city = "City / Town is required.";
                        if (!state.country?.trim()) errors.country = "Country is required.";

                        const ukAddress = (state.country || "").toLowerCase().includes("united kingdom") || (state.country || "").toLowerCase().includes("uk");
                        if (ukAddress && !state.postcode?.trim()) errors.postcode = "Postcode is required for UK addresses.";
                        if (ukAddress && !state.county?.trim()) errors.county = "County is required for UK addresses.";

                        if (!state.proofOfAddressFile) {
                            errors.proofOfAddress = "Please upload a proof of address before continuing.";
                        }

                        setValidationErrors(errors);
                        if (Object.keys(errors).length > 0) return;

                        // If already verified (e.g. going back and forward), skip re-verification
                        if (addressVerified) {
                            next();
                            return;
                        }

                        // 1. Create the address via API, then 2. verify with proof of address
                        setVerifying(true);
                        try {
                            const voterId = state.voterId;
                            if (!voterId) {
                                setValidationErrors({ proofOfAddress: "Voter record not found. Please go back and complete identity verification." });
                                setVerifying(false);
                                return;
                            }

                            // Step 1: Create the address (starts as PENDING)
                            let addressId = state.addressId;
                            if (!addressId) {
                                const isOverseas = (state.region || "").toLowerCase() === "overseas";
                                const addr = await voterApi.createAddress(voterId, {
                                    address_type: isOverseas ? AddressType.OVERSEAS : AddressType.LOCAL_CURRENT,
                                    address_line1: state.addressLine1 || "",
                                    address_line2: state.addressLine2 || undefined,
                                    city: state.city || "",
                                    postcode: state.postcode || "",
                                    county: state.county || "",
                                    country: state.country || "",
                                });
                                addressId = addr.id;
                                setState((prev: any) => ({ ...prev, addressId }));
                            }

                            // Step 2: Upload proof of address for OCR verification against stored address
                            const data = await voterApi.verifyAddress(voterId, addressId, state.proofOfAddressFile);

                            if (data.status === "verified") {
                                setAddressVerified(true);
                                setState((prev: any) => ({ ...prev, addressVerified: true }));
                                setVerifying(false);
                                next();
                            } else {
                                const details = data.details || {};
                                const failedFields = Object.entries(details)
                                    .filter(([, v]) => !v)
                                    .map(([k]) => k.replace("_", " "))
                                    .join(", ");
                                setValidationErrors({
                                    proofOfAddress: `Address verification failed. The following could not be found in your document: ${failedFields}. Please upload a clearer document or check your address details.`,
                                });
                                setVerifying(false);
                            }
                        } catch (err: any) {
                            setValidationErrors({ proofOfAddress: err.message || "Failed to verify address. Please try again." });
                            setVerifying(false);
                        }
                    }}
                >
                    {verifying ? "Verifying address\u2026" : primaryButtonLabel}
                </PrimaryButton>
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