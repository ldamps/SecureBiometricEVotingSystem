/**
 * Primary and Secondary button components.
 */

import React from "react";
import { useTheme } from "../ThemeContext";
import {
  getPrimaryButtonStyle,
  getPrimaryButtonHoverStyle,
  getSecondaryButtonStyle,
  getSecondaryButtonHoverStyle,
  type ButtonProps,
} from "./button";

/**
 * Primary CTA button. Use for main actions (Next, Submit, etc.).
 */
export const PrimaryButton: React.FC<ButtonProps> = ({
  children,
  onClick,
  type = "button",
  disabled = false,
  className = "",
}) => {
  const { theme } = useTheme();
  const [hover, setHover] = React.useState(false);
  const base = getPrimaryButtonStyle(theme);
  const hoverStyle = hover && !disabled ? getPrimaryButtonHoverStyle(theme) : {};
  return (
    <button
      type={type}
      className={className.trim() || undefined}
      style={{ ...base, ...hoverStyle }}
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      disabled={disabled}
    >
      {children}
    </button>
  );
};

/**
 * Secondary button. Smaller and distinct colour (outline style). Use for secondary actions (e.g. Upload file).
 */
export const SecondaryButton: React.FC<ButtonProps> = ({
  children,
  onClick,
  type = "button",
  disabled = false,
  className = "",
}) => {
  const { theme } = useTheme();
  const [hover, setHover] = React.useState(false);
  const base = getSecondaryButtonStyle(theme);
  const hoverStyle = hover && !disabled ? getSecondaryButtonHoverStyle(theme) : {};
  return (
    <button
      type={type}
      className={className.trim() || undefined}
      style={{ ...base, ...hoverStyle }}
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      disabled={disabled}
    >
      {children}
    </button>
  );
};
