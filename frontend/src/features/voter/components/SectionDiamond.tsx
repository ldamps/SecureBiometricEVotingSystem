import React from "react";
import { useTheme } from "../../../styles/ThemeContext";
import { getSectionIconStyle } from "../../../features/voter/components/voterStyles";

const SectionDiamond: React.FC = () => {
  const { theme } = useTheme();
  const sectionIconStyle = getSectionIconStyle(theme);
  return (
    <svg
      width="0.65em"
      height="0.65em"
      viewBox="0 0 24 24"
      style={sectionIconStyle}
      aria-hidden
    >
      <rect
        x="4"
        y="4"
        width="16"
        height="16"
        rx="2"
        transform="rotate(45 12 12)"
      />
    </svg>
  );
};

export default SectionDiamond;
