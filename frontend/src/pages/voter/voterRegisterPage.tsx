import LivingDetails from "../../features/voter/components/livingDetails";
import React, { useState } from "react";
import RegistrationDetails from "../../features/voter/components/registrationDetails";
import { useTheme } from "../../styles/ThemeContext";
import CurrentAddress from "../../features/voter/components/currentAddress";
import BiometricRegistration from "../../features/voter/components/biometricRegistration";
import RegistrationConfirmation from "../../features/voter/components/registrationConfirmation";

const VoterRegisterPage: React.FC = () => {
    const { theme } = useTheme();
    const { colors, spacing, fonts } = theme;
    const [step, setStep] = useState(1);
    const [state, setState] = useState({
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
        nameChanged: false,
        previousFirstName: "",
        previousLastName: "",
        address_line_1: "",
        address_line_2: "",
        city: "",
        postcode: "",
        county: "",
        country: "",
    });

    const next = () => setStep(s => Math.min(s + 1, 5));
    const previous = () => setStep(s => Math.max(s - 1, 1));

    const pages = [
        <LivingDetails next={next} state={state} setState={setState} />,
        <RegistrationDetails next={next} back={previous} state={state} setState={setState} />,
        <CurrentAddress next={next} back={previous} state={state} setState={setState} />,
        <BiometricRegistration next={next} back={previous} state={state} setState={setState} />,
        <RegistrationConfirmation next={next} back={previous} state={state} setState={setState} />,
    ]

    return (
        <div
            style={{
                minHeight: `calc(100vh - 72px)`,
                backgroundColor: colors.background,
                color: colors.text.primary,
                fontFamily: fonts.body,
                padding: spacing["2xl"],
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "flex-start",
            }}
        >
            <div style={{ width: "100%", maxWidth: "480px", margin: "0 auto" }}>
                {pages[step-1]}
            </div>
        </div>
    )
}

export default VoterRegisterPage;