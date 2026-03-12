/**
 * Reusable header and heading styles – page title, section h2, h3, paragraph after header.
 */

import type { Theme } from "../theme";

/** Page title (h1) */
export const getPageTitleStyle = (theme: Theme) => ({
  fontSize: theme.fontSizes["3xl"],
  fontWeight: theme.fontWeights.bold,
  color: theme.colors.text.primary,
  marginBottom: 0,
  marginTop: 0,
  lineHeight: 1.2,
  paddingLeft: theme.spacing.xl,
  paddingRight: theme.spacing.xl,
  paddingTop: theme.spacing.xl,
  paddingBottom: theme.spacing.sm,
});

/** Section heading (h2) */
export const getSectionH2Style = (theme: Theme) => ({
  fontSize: theme.fontSizes["2xl"],
  fontWeight: theme.fontWeights.bold,
  color: theme.colors.text.primary,
  marginBottom: 0,
  lineHeight: 1.2,
  paddingLeft: theme.spacing.xl,
  paddingRight: theme.spacing.xl,
  paddingTop: 0,
  paddingBottom: theme.spacing.xs,
});

/** H3 with icon alignment – for subsections */
export const getH3Style = (theme: Theme) => ({
  fontSize: theme.fontSizes.xl,
  fontWeight: theme.fontWeights.bold,
  color: theme.colors.text.primary,
  marginBottom: 0,
  lineHeight: 1.2,
  paddingLeft: theme.spacing.xl,
  paddingRight: theme.spacing.xl,
  paddingTop: theme.spacing.md,
  paddingBottom: theme.spacing.xs,
  display: "flex" as const,
  alignItems: "center" as const,
});

/** Paragraph immediately after a heading */
export const getPAfterHeaderStyle = (theme: Theme) => ({
  fontSize: theme.fontSizes.xl,
  color: theme.colors.text.secondary,
  lineHeight: 1.6,
  paddingLeft: theme.spacing.xl,
  paddingRight: theme.spacing.xl,
  paddingTop: theme.spacing.xs,
  paddingBottom: theme.spacing.md,
});
