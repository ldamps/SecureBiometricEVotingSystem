/**
 * Reusable styles for multi-step flows (e.g. vote casting steps).
 * Use with useTheme() in components.
 */

import type { Theme } from "../theme";

/** Step title (h1/h2) in a wizard/step flow */
export const getStepTitleStyle = (theme: Theme) => ({
  fontSize: theme.fontSizes["2xl"],
  fontWeight: theme.fontWeights.bold,
  color: theme.colors.text.primary,
  marginBottom: theme.spacing.xs,
  marginTop: 0,
});

/** Step description paragraph below the title */
export const getStepDescStyle = (theme: Theme) => ({
  fontSize: theme.fontSizes.base,
  color: theme.colors.text.secondary,
  lineHeight: 1.6,
  marginBottom: theme.spacing.lg,
});

/** Text input in step forms (e.g. voter identity fields) */
export const getStepFormInputStyle = (theme: Theme) => ({
  width: "100%",
  padding: theme.spacing.sm,
  fontSize: theme.fontSizes.base,
  color: theme.colors.text.primary,
  backgroundColor: theme.colors.surface,
  border: `1px solid ${theme.colors.border}`,
  borderRadius: theme.borderRadius.md,
  marginTop: theme.spacing.xs,
});

/** Label for form fields in step flows */
export const getStepLabelStyle = (theme: Theme) => ({
  fontSize: theme.fontSizes.sm,
  fontWeight: theme.fontWeights.medium,
  color: theme.colors.text.primary,
});
