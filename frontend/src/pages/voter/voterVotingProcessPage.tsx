import React from "react";
import { useTheme } from "../../styles/ThemeContext";
import { VoterPageWrapper, VoterPageHeader } from "../../features/components";

const VoterVotingProcessPage: React.FC = () => {
    const { theme } = useTheme();

    return (
        <div className="voter-voting-process-page">
            <style>{`
                .voter-voting-process-page a:hover { color: ${theme.colors.primaryHover}; }
            `}</style>
            <VoterPageWrapper className="voter-voting-process-page">
                <VoterPageHeader title="The Voting Process" />
            </VoterPageWrapper>
        </div>
    )
}

export default VoterVotingProcessPage;