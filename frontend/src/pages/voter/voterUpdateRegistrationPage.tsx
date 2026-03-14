import React, { useState, useCallback } from "react";
import {
    getFirstSectionStyle,
    getPageTitleStyle,
    getVoterPageContentWrapperStyle,
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
};

const VoterUpdateRegistrationPage: React.FC = () => {
    const { theme } = useTheme();
    const firstSectionStyle = getFirstSectionStyle(theme);
    const [verificationPhase, setVerificationPhase] = useState<VerificationPhase>("identity");
    const [activeSection, setActiveSection] = useState<UpdateSection>(null);
    const [state, setState] = useState<Record<string, unknown>>(initialState);
    const navigate = useNavigate();
    const setStateTyped = useCallback((s: Record<string, unknown>) => {
        setState(s);
    }, []);

    const afterIdentity = () => setVerificationPhase("biometric");
    const afterBiometric = () => setVerificationPhase("verified");

    const backToHub = () => setActiveSection(null);

    const handleSaveDraft = () => {
        // Draft is already in state; optionally persist or call API here
        backToHub();
    };

    const handleSaveChanges = () => {
        // Hook for API: state holds identity confirmation + all update sections
        console.log("Update registration submit", state);
        navigate("/voter/landing");
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
                next={handleSaveDraft}
                back={backToHub}
                state={state}
                setState={setStateTyped}
                progressStep={3}
                heading="Update: Identity details"
                showProgressBar={false}
                primaryButtonLabel="Save draft"
                usePageLayout
            />
        );
    }

    if (activeSection === "address") {
        return (
            <CurrentAddress
                next={handleSaveDraft}
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
                next={handleSaveDraft}
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
                <div
                    style={{
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "flex-start",
                        gap: theme.spacing.md,
                    }}
                >
                    <SecondaryButton type="button" onClick={() => setActiveSection("identity")}>
                        Update your identity details
                    </SecondaryButton>
                    <SecondaryButton type="button" onClick={() => setActiveSection("address")}>
                        Update your current address
                    </SecondaryButton>
                    <SecondaryButton type="button" onClick={() => setActiveSection("biometric")}>
                        Renew your biometric details
                    </SecondaryButton>
                </div>
                <br />
                <p style={{ marginBottom: theme.spacing.sm }}>
                    To save these changes, press Save changes when you are finished editing the sections you need.
                </p>
                <p style={{ marginBottom: theme.spacing.sm }}>
                    Your requested changes will be processed within 24 hours and you will receive an email             confirmation when they are complete.
                </p>
                <p style={{ marginBottom: 0 }}>
                    If you have any questions or concerns, please contact your local electoral office.
                </p>
                <br />
                <div style={{ display: "flex", justifyContent: "left", gap: theme.spacing.md }}>
                <PrimaryButton type="button" onClick={handleSaveChanges}>
                    Save changes
                </PrimaryButton>
                <PrimaryButton type="button" onClick={() => navigate("/voter/landing")}>Cancel</PrimaryButton>
                </div>
            </section>
        </div>
    );
};

export default VoterUpdateRegistrationPage;
