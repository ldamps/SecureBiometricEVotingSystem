import React from "react";
import { useTheme } from "../../../styles/ThemeContext";
import { getPageTitleStyle } from "../../../features/voter/components/voterStyles";

interface VoterPageHeaderProps {
  title: string;
}

const VoterPageHeader: React.FC<VoterPageHeaderProps> = ({ title }) => {
  const { theme } = useTheme();
  const pageTitleStyle = getPageTitleStyle(theme);
  return (
    <header>
      <h1 style={pageTitleStyle}>{title}</h1>
    </header>
  );
};

export default VoterPageHeader;
