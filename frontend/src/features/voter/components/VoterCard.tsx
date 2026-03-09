import React from "react";
import { useTheme } from "../../../styles/ThemeContext";
import {
  getRegistrationCardStyle,
  getRegistrationCardTitleStyle,
} from "../../../features/voter/components/voterStyles";

interface VoterCardProps {
  title: string;
  children: React.ReactNode;
  style?: React.CSSProperties;
}

const VoterCard: React.FC<VoterCardProps> = ({ title, children, style: styleOverride }) => {
  const { theme } = useTheme();
  const cardStyle = getRegistrationCardStyle(theme);
  const cardTitleStyle = getRegistrationCardTitleStyle(theme);
  return (
    <div style={{ ...cardStyle, ...styleOverride }}>
      <h2 style={cardTitleStyle}>{title}</h2>
      {children}
    </div>
  );
};

export default VoterCard;
