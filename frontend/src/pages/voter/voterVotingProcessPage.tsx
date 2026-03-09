import React from "react";
import { useTheme } from "../../styles/ThemeContext";
import { getPageTitleStyle, getVoterPageContentWrapperStyle } from "../../styles/ui";

const VoterVotingProcessPage: React.FC = () => {
  const { theme } = useTheme();
  const pageTitleStyle = getPageTitleStyle(theme);
  const wrapperStyle = getVoterPageContentWrapperStyle(theme);

  return (
    <div className="voter-voting-process-page">
      <style>{`
        .voter-voting-process-page a:hover { color: ${theme.colors.primaryHover}; }
      `}</style>
      <div className="voter-voting-process-page voter-page-content" style={wrapperStyle}>
        <header>
          <h1 style={pageTitleStyle}>The Voting Process</h1>
        </header>
      </div>
    </div>
  );
};

export default VoterVotingProcessPage;
