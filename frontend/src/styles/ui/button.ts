/**
 * Button style getters. Components are in buttonComponents.tsx.
 */

import type { CSSProperties, ReactNode } from "react";
import type { Theme } from "../theme";

export const getPrimaryButtonStyle = (theme: Theme): CSSProperties => ({
  backgroundColor: theme.colors.button,
  color: theme.colors.text.inverse,
  border: "none",
  borderRadius: theme.borderRadius.md,
  cursor: "pointer",
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  textAlign: "center",
  lineHeight: 1.3,
  padding: `${theme.spacing.md} ${theme.spacing.xl}`,
  fontSize: theme.fontSizes.base,
  fontWeight: theme.fontWeights.bold,
  boxShadow: theme.colors.shadows.md,
  transition: "background-color 0.2s ease, transform 0.15s ease, box-shadow 0.2s ease",
});

export const getPrimaryButtonHoverStyle = (theme: Theme): CSSProperties => ({
  backgroundColor: theme.colors.primaryHover,
  transform: "translateY(-2px)",
  boxShadow: theme.colors.shadows.lg,
});

export const getSecondaryButtonStyle = (theme: Theme): CSSProperties => ({
  backgroundColor: theme.colors.surface,
  color: theme.colors.secondary,
  border: `2px solid ${theme.colors.secondary}`,
  borderRadius: theme.borderRadius.md,
  cursor: "pointer",
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  textAlign: "center",
  lineHeight: 1.3,
  padding: theme.spacing.sm,
  fontSize: theme.fontSizes.sm,
  fontWeight: theme.fontWeights.semibold,
  transition: "background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease, transform 0.15s ease",
});

export const getSecondaryButtonHoverStyle = (theme: Theme): CSSProperties => ({
  backgroundColor: theme.colors.secondary,
  color: theme.colors.text.inverse,
  borderColor: theme.colors.secondary,
  transform: "translateY(-1px)",
});

export interface ButtonProps {
  children: ReactNode;
  onClick?: () => void;
  type?: "button" | "submit" | "reset";
  disabled?: boolean;
  className?: string;
}
