import { useState } from "react";
import { useTheme } from "../../styles/ThemeContext";
import ElectionSelection from "../../features/election/components/electionSelection";
import VoterIdentity from "../../features/voter/components/voterIdentity";
import BiometricVerification from "../../features/voter/components/biometricVerification";
import CandidateSelection from "../../features/voter/components/candidateSelection";
import VoteConfirmation from "../../features/voter/components/voteConfirmation";

const VoteCastingPage = () => {
    const { theme } = useTheme();
    const { colors, spacing, fonts } = theme;
    const [step, setStep] = useState(1);
    const [state, setState] = useState({
        election:"", name:"", addr1:"", addr2:"", city:"", postcode:"", county:"", candidate:""
    });

    const next = () => setStep(s => Math.min(s+1, 5));

    const pages = [
        <ElectionSelection next={next} state={state} setState={setState} />,
        <VoterIdentity next={next} state={state} setState={setState} />,
        <BiometricVerification next={next} state={state} setState={setState} />,
        <CandidateSelection next={next} state={state} setState={setState} />,
        <VoteConfirmation next={next} state={state} setState={setState} />
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
            <div
                style={{
                    width: "100%",
                    maxWidth: step === 1 ? "min(100%, 52rem)" : "480px",
                    margin: "0 auto",
                }}
            >
                {pages[step-1]}
            </div>
        </div>
    )
}

export default VoteCastingPage;