import { useState, useEffect, useRef, useCallback } from "react";
import { useTheme } from "../../styles/ThemeContext";
import { useNavigate } from "react-router-dom";
import ElectionSelection from "../../features/election/components/electionSelection";
import VoterIdentity from "../../features/voter/components/voterIdentity";
import BiometricVerification from "../../features/voter/components/biometricVerification";
import CandidateSelection from "../../features/voter/components/candidateSelection";
import ReferendumAnswerSelection from "../../features/voter/components/referendumAnswerSelection";
import VoteConfirmation from "../../features/voter/components/voteConfirmation";

/** Duration of the voting timer in seconds (starts after biometric verification). */
const VOTE_TIMER_SECONDS = 10 * 60; // 10 minutes

const VoteCastingPage = () => {
    const { theme } = useTheme();
    const { colors, spacing, fonts } = theme;
    const navigate = useNavigate();
    const [step, setStep] = useState(1);
    const [state, setState] = useState<Record<string, unknown>>({
        // VoterIdentity
        name: "", addr1: "", addr2: "", city: "", postcode: "",
        voterId: "", constituencyId: "",
        // BiometricVerification
        biometricVerified: false,
        // ElectionSelection
        election: "", referendum: "",
        // CandidateSelection / ReferendumAnswerSelection
        candidateId: "", partyId: "", rankings: {} as Record<string, number>,
        referendumChoice: "",
    });

    // ---- 10-minute voting timer (starts at step 3, after biometric) ----
    const [timeLeft, setTimeLeft] = useState<number | null>(null);
    const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const [timerExpired, setTimerExpired] = useState(false);

    const startTimer = useCallback(() => {
        if (timerRef.current) clearInterval(timerRef.current);
        setTimeLeft(VOTE_TIMER_SECONDS);
        setTimerExpired(false);
        timerRef.current = setInterval(() => {
            setTimeLeft((prev) => {
                if (prev === null || prev <= 1) {
                    if (timerRef.current) clearInterval(timerRef.current);
                    setTimerExpired(true);
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);
    }, []);

    // Start timer when entering step 3
    useEffect(() => {
        if (step === 3 && timeLeft === null) {
            startTimer();
        }
    }, [step, timeLeft, startTimer]);

    // Clean up timer on unmount
    useEffect(() => {
        return () => {
            if (timerRef.current) clearInterval(timerRef.current);
        };
    }, []);

    // Redirect when timer expires
    useEffect(() => {
        if (timerExpired) {
            navigate("/voter/landing");
        }
    }, [timerExpired, navigate]);

    // ---- navigation ----
    const next = () => setStep(s => Math.min(s + 1, 5));
    const previous = () => setStep(s => Math.max(s - 1, 1));
    const isReferendum = Boolean(state.referendum);

    // ---- prevent back-navigation after vote submission ----
    const [voteSubmitted, setVoteSubmitted] = useState(false);

    useEffect(() => {
        if (!voteSubmitted) return;
        const handlePopState = () => {
            // Push state again to prevent going back
            window.history.pushState(null, "", window.location.href);
        };
        window.history.pushState(null, "", window.location.href);
        window.addEventListener("popstate", handlePopState);
        return () => window.removeEventListener("popstate", handlePopState);
    }, [voteSubmitted]);

    // Wrap VoteConfirmation's next to mark submission
    const onVoteSubmitted = () => {
        setVoteSubmitted(true);
        if (timerRef.current) clearInterval(timerRef.current);
    };

    const formatTime = (seconds: number) => {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return `${m}:${String(s).padStart(2, "0")}`;
    };

    const pages = [
        <VoterIdentity next={next} state={state} setState={setState} />,
        <BiometricVerification next={next} state={state} setState={setState} />,
        <ElectionSelection next={next} state={state} setState={setState} />,
        isReferendum
            ? <ReferendumAnswerSelection next={next} back={previous} state={state} setState={setState} />
            : <CandidateSelection next={next} back={previous} state={state} setState={setState} />,
        <VoteConfirmation next={onVoteSubmitted} state={state} setState={setState} />,
    ];

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
            {/* Timer banner — shown from step 3 onwards */}
            {timeLeft !== null && step >= 3 && !voteSubmitted && (
                <div style={{
                    width: "100%",
                    maxWidth: step === 1 ? "min(100%, 52rem)" : "480px",
                    margin: "0 auto 1rem auto",
                    padding: "0.5rem 1rem",
                    borderRadius: "6px",
                    textAlign: "center",
                    fontSize: "0.9rem",
                    fontWeight: 600,
                    backgroundColor: timeLeft <= 60 ? "#fef2f2" : "#fffbeb",
                    border: `1px solid ${timeLeft <= 60 ? "#dc2626" : "#f59e0b"}`,
                    color: timeLeft <= 60 ? "#dc2626" : "#b45309",
                }}>
                    {timeLeft <= 60
                        ? `Warning: ${formatTime(timeLeft)} remaining to cast your vote!`
                        : `Time remaining: ${formatTime(timeLeft)}`
                    }
                </div>
            )}
            <div
                style={{
                    width: "100%",
                    maxWidth: step === 1 ? "min(100%, 52rem)" : "480px",
                    margin: "0 auto",
                }}
            >
                {pages[step - 1]}
            </div>
        </div>
    );
};

export default VoteCastingPage;
