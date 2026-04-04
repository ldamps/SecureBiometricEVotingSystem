import React, { useState, useCallback, useEffect } from "react";
import {
    getCardStyle,
    getFirstSectionStyle,
    getPageTitleStyle,
    getVoterPageContentWrapperStyle,
    getErrorAlertStyle,
    getSuccessAlertStyle,
    PrimaryButton,
    SecondaryButton,
} from "../../styles/ui";
import { useTheme } from "../../styles/ThemeContext";
import VoterIdentity from "../../features/voter/components/voterIdentity";
import BiometricVerification from "../../features/voter/components/biometricVerification";
import RegistrationDetails from "../../features/voter/components/registrationDetails";
import CurrentAddress from "../../features/voter/components/currentAddress";
import BiometricRegistration from "../../features/voter/components/biometricRegistration";
import { useNavigate } from "react-router-dom";
import { VoterApiRepository } from "../../features/voter/repositories/voter-api.repository";
import { NationalityCategory } from "../../features/voter/model/voter.model";

const voterApi = new VoterApiRepository();

type VerificationPhase = "identity" | "biometric" | "verified";
type UpdateSection = null | "identity" | "address" | "biometric";

const initialState: Record<string, unknown> = {
    // VoterIdentity (confirm)
    name: "",
    addr1: "",
    addr2: "",
    city: "",
    postcode: "",
    // RegistrationDetails
    firstName: "",
    lastName: "",
    email: "",
    dateOfBirth: "",
    nationalInsuranceNumber: "",
    passportNumber: "",
    passportCountry: "",
    passportExpiryDate: "",
    nationalityBritish: false,
    nationalityIrish: false,
    nationalityOtherCountry: false,
    otherCountries: "",
    nameChanged: null as boolean | null,
    previousFirstName: "",
    previousLastName: "",
    // CurrentAddress
    addressLine1: "",
    addressLine2: "",
    county: "",
    country: "",
    proofOfAddressFileName: "",
    // Tracking existing values for change detection
    existingNI: "",
    existingPassportNumber: "",
    existingPassportId: "",
    existingAddressId: "",
};

const VoterUpdateRegistrationPage: React.FC = () => {
    const { theme } = useTheme();
    const firstSectionStyle = getFirstSectionStyle(theme);
    const [verificationPhase, setVerificationPhase] = useState<VerificationPhase>("identity");
    const [activeSection, setActiveSection] = useState<UpdateSection>(null);
    const [state, setState] = useState<Record<string, unknown>>(initialState);
    const [editedSections, setEditedSections] = useState<Set<string>>(new Set());
    const [saving, setSaving] = useState(false);
    const [saveError, setSaveError] = useState<string | null>(null);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [stateSnapshot, setStateSnapshot] = useState<Record<string, unknown> | null>(null);
    const navigate = useNavigate();

    const setStateTyped = useCallback((s: Record<string, unknown> | ((prev: Record<string, unknown>) => Record<string, unknown>)) => {
        if (typeof s === "function") {
            setState(s);
        } else {
            setState(s);
        }
    }, []);

    // After identity + biometric verification, load the voter's existing data
    useEffect(() => {
        if (verificationPhase !== "verified") return;
        const voterId = state.voterId as string;
        if (!voterId) return;

        let cancelled = false;

        const loadVoterData = async () => {
            const [voter, addresses] = await Promise.all([
                voterApi.getVoter(voterId),
                voterApi.listAddresses(voterId),
            ]);

            if (cancelled) return;

            const primaryPassport = voter.passports?.find((p) => p.is_primary) ?? voter.passports?.[0];
            const currentAddress = addresses.find(
                (a) => a.address_type === "LOCAL_CURRENT" || a.address_type === "OVERSEAS",
            ) ?? addresses[0];

            const natBritish = voter.nationality_category === NationalityCategory.BRITISH_CITIZEN;
            const natIrish = voter.nationality_category === NationalityCategory.IRISH_CITIZEN;
            const natOther = !natBritish && !natIrish && voter.nationality_category !== undefined;

            setState((prev) => ({
                ...prev,
                // Identity details
                firstName: voter.first_name || "",
                lastName: voter.surname || "",
                email: voter.email || "",
                dateOfBirth: voter.date_of_birth || "",
                nationalInsuranceNumber: voter.national_insurance_number || "",
                identificationMethod: voter.national_insurance_number ? "ni" : primaryPassport ? "passport" : "",
                passportNumber: primaryPassport?.passport_number || "",
                passportCountry: primaryPassport?.issuing_country || "",
                passportExpiryDate: primaryPassport?.expiry_date || "",
                nationalityBritish: natBritish,
                nationalityIrish: natIrish,
                nationalityOtherCountry: natOther,
                nameChanged: !!(voter.previous_first_name || voter.previous_surname),
                previousFirstName: voter.previous_first_name || "",
                previousLastName: voter.previous_surname || "",
                // Address details
                addressLine1: currentAddress?.address_line1 || "",
                addressLine2: currentAddress?.address_line2 || "",
                city: currentAddress?.city || "",
                postcode: currentAddress?.postcode || "",
                county: currentAddress?.county || "",
                country: currentAddress?.country || "",
                // Existing values for change detection
                existingNI: voter.national_insurance_number || "",
                existingPassportNumber: primaryPassport?.passport_number || "",
                existingPassportId: primaryPassport?.id || "",
                existingAddressId: currentAddress?.id || "",
            }));
        };

        loadVoterData().catch(() => {
            // Non-fatal — form starts empty, user can still fill in changes
        });

        return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [verificationPhase]);

    const afterIdentity = () => setVerificationPhase("biometric");
    const afterBiometric = () => setVerificationPhase("verified");

    const openSection = (section: UpdateSection) => {
        setStateSnapshot({ ...state });
        setActiveSection(section);
    };

    const backToHub = () => {
        if (stateSnapshot) {
            setState(stateSnapshot);
            setStateSnapshot(null);
        }
        setActiveSection(null);
    };

    const handleSaveDraft = (section: string) => () => {
        setStateSnapshot(null);
        setEditedSections((prev) => new Set(prev).add(section));
        setSaveSuccess(false);
        setSaveError(null);
        setActiveSection(null);
    };

    const handleSaveChanges = async () => {
        if (saving) return;

        const voterId = state.voterId as string;
        if (!voterId) {
            setSaveError("Voter record not found. Please verify your identity again.");
            return;
        }

        if (editedSections.size === 0) {
            setSaveError("No changes to save. Please edit at least one section before saving.");
            return;
        }

        setSaving(true);
        setSaveError(null);
        setSaveSuccess(false);

        const errors: string[] = [];

        // Save identity details
        if (editedSections.has("identity")) {
            try {
                let natCat: NationalityCategory | undefined;
                if (state.nationalityBritish) natCat = NationalityCategory.BRITISH_CITIZEN;
                else if (state.nationalityIrish) natCat = NationalityCategory.IRISH_CITIZEN;
                else if (state.nationalityOtherCountry) natCat = NationalityCategory.OTHER;

                await voterApi.updateVoter(voterId, {
                    first_name: (state.firstName as string) || undefined,
                    surname: (state.lastName as string) || undefined,
                    previous_first_name: state.nameChanged ? (state.previousFirstName as string) || undefined : undefined,
                    previous_surname: state.nameChanged ? (state.previousLastName as string) || undefined : undefined,
                    date_of_birth: (state.dateOfBirth as string) || undefined,
                    email: (state.email as string) || undefined,
                    nationality_category: natCat,
                });

                // Handle passport changes
                const passportNumber = (state.passportNumber as string || "").trim();
                const existingPassportNumber = (state.existingPassportNumber as string || "").trim();
                const existingPassportId = (state.existingPassportId as string || "").trim();

                if (state.identificationMethod === "passport" && passportNumber) {
                    if (existingPassportId && passportNumber !== existingPassportNumber) {
                        await voterApi.updatePassport(voterId, existingPassportId, {
                            passport_number: passportNumber,
                            issuing_country: (state.passportCountry as string) || undefined,
                            expiry_date: (state.passportExpiryDate as string) || undefined,
                        });
                    } else if (!existingPassportId) {
                        await voterApi.createPassport(voterId, {
                            passport_number: passportNumber,
                            issuing_country: (state.passportCountry as string) || "GB",
                            expiry_date: (state.passportExpiryDate as string) || undefined,
                            is_primary: true,
                        });
                    }
                }
            } catch (err: any) {
                errors.push(`Identity details: ${err.message || "Failed to save changes."}`);
            }
        }

        // Address changes are already persisted by the CurrentAddress component
        // (it creates a new LOCAL_CURRENT address, which demotes the old one to PAST,
        // then verifies it via proof-of-address upload). No additional API call needed.

        setSaving(false);

        if (errors.length > 0) {
            setSaveError(errors.join(" "));
        } else {
            setSaveSuccess(true);
            setEditedSections(new Set());
            setTimeout(() => navigate("/voter/landing"), 2000);
        }
    };

    if (verificationPhase === "identity") {
        return (
            <VoterIdentity
                next={afterIdentity}
                state={state}
                setState={setStateTyped}
                progressStep={1}
                showProgressBar={false}
                usePageLayout
            />
        );
    }

    if (verificationPhase === "biometric") {
        return (
            <BiometricVerification
                next={afterBiometric}
                state={state}
                setState={setStateTyped}
                progressStep={2}
                showProgressBar={false}
                usePageLayout
            />
        );
    }

    if (activeSection === "identity") {
        return (
            <RegistrationDetails
                next={handleSaveDraft("identity")}
                back={backToHub}
                state={state}
                setState={setStateTyped}
                progressStep={3}
                heading="Update: Identity details"
                showProgressBar={false}
                primaryButtonLabel="Save draft"
                usePageLayout
                isUpdate
                existingNI={(state.existingNI as string) || ""}
                existingPassportNumber={(state.existingPassportNumber as string) || ""}
            />
        );
    }

    if (activeSection === "address") {
        return (
            <CurrentAddress
                next={handleSaveDraft("address")}
                back={backToHub}
                state={state}
                setState={setStateTyped}
                progressStep={4}
                heading="Update: Current address"
                showProgressBar={false}
                primaryButtonLabel="Save draft"
                usePageLayout
            />
        );
    }

    if (activeSection === "biometric") {
        return (
            <BiometricRegistration
                next={handleSaveDraft("biometric")}
                back={backToHub}
                state={state}
                setState={setStateTyped}
                progressStep={5}
                heading="Renew: Biometric details"
                showProgressBar={false}
                primaryButtonLabel="Save draft"
                usePageLayout
            />
        );
    }

    const sectionLabel = (section: string, label: string) => (
        <span>
            {label}
            {editedSections.has(section) && (
                <span style={{ marginLeft: "0.5rem", fontSize: "0.8rem", color: theme.colors.status.warning ?? "#d97706" }}>
                    (draft)
                </span>
            )}
        </span>
    );

    return (
        <div
            className="voter-update-registration-page voter-page-content"
            style={getVoterPageContentWrapperStyle(theme)}
        >
            <header>
                <h1 style={getPageTitleStyle(theme)}>Update your registration details</h1>
            </header>
            <section style={firstSectionStyle}>
                <p style={{ marginBottom: theme.spacing.md }}>
                    You have confirmed your identity. Select what you would like to update:
                </p>

                {saveError && (
                    <div style={{ ...getCardStyle(theme), ...getErrorAlertStyle(theme), marginBottom: "1rem" }}>
                        <p style={{ color: theme.colors.status.error, fontSize: "0.9rem", fontWeight: 600, margin: 0 }}>
                            {saveError}
                        </p>
                    </div>
                )}

                {saveSuccess && (
                    <div style={{ ...getCardStyle(theme), ...getSuccessAlertStyle(theme), marginBottom: "1rem" }}>
                        <p style={{ color: theme.colors.status.success, fontSize: "0.9rem", fontWeight: 600, margin: 0 }}>
                            Your changes have been saved successfully. Redirecting...
                        </p>
                    </div>
                )}

                <div
                    style={{
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "flex-start",
                        gap: theme.spacing.md,
                    }}
                >
                    <SecondaryButton type="button" onClick={() => openSection("identity")}>
                        {sectionLabel("identity", "Update your identity details")}
                    </SecondaryButton>
                    <SecondaryButton type="button" onClick={() => openSection("address")}>
                        {sectionLabel("address", "Update your current address")}
                    </SecondaryButton>
                    <SecondaryButton type="button" onClick={() => openSection("biometric")}>
                        {sectionLabel("biometric", "Renew your biometric details")}
                    </SecondaryButton>
                </div>
                <br />
                <p style={{ marginBottom: theme.spacing.sm }}>
                    To save these changes, press Save changes when you are finished editing the sections you need.
                </p>
                <p style={{ marginBottom: theme.spacing.sm }}>
                    Your requested changes will be processed within 24 hours and you will receive an email confirmation when they are complete.
                </p>
                <p style={{ marginBottom: 0 }}>
                    If you have any questions or concerns, please contact your local electoral office.
                </p>
                <br />
                <div style={{ display: "flex", justifyContent: "left", gap: theme.spacing.md }}>
                    <PrimaryButton type="button" disabled={saving} onClick={handleSaveChanges}>
                        {saving ? "Saving..." : "Save changes"}
                    </PrimaryButton>
                    <PrimaryButton type="button" onClick={() => navigate("/voter/landing")}>Cancel</PrimaryButton>
                </div>
            </section>
        </div>
    );
};

export default VoterUpdateRegistrationPage;
