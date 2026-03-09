import React from "react";
import { useTheme } from "../../styles/ThemeContext";
import { getFirstSectionStyle } from "./voterStyles";

interface VoterFirstSectionProps {
  children: React.ReactNode;
  as?: "div" | "p";
}

const VoterFirstSection: React.FC<VoterFirstSectionProps> = ({
  children,
  as: Tag = "p",
}) => {
  const { theme } = useTheme();
  const style = getFirstSectionStyle(theme);
  return <Tag style={style}>{children}</Tag>;
};

export default VoterFirstSection;
