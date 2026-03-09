import React from "react";
import { useTheme } from "../../styles/ThemeContext";
import { getVoterPageContentWrapperStyle } from "./voterStyles";

interface VoterPageWrapperProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

const VoterPageWrapper: React.FC<VoterPageWrapperProps> = ({
  children,
  className = "",
  style,
}) => {
  const { theme } = useTheme();
  const wrapperStyle = getVoterPageContentWrapperStyle(theme);
  return (
    <div
      className={`voter-page-content ${className}`.trim()}
      style={{ ...wrapperStyle, ...style }}
    >
      {children}
    </div>
  );
};

export default VoterPageWrapper;
