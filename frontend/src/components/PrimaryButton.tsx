import React from "react";

interface PrimaryButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  type?: "button" | "submit" | "reset";
  disabled?: boolean;
  className?: string;
}

/**
 * Standardized primary CTA button. Use across pages; only the label (children) and action (onClick) change.
 * Styling and hover are handled by the global .button-base class.
 */
const PrimaryButton: React.FC<PrimaryButtonProps> = ({
  children,
  onClick,
  type = "button",
  disabled = false,
  className = "",
}) => (
  <button
    type={type}
    className={`button-base ${className}`.trim()}
    onClick={onClick}
    disabled={disabled}
  >
    {children}
  </button>
);

export default PrimaryButton;
