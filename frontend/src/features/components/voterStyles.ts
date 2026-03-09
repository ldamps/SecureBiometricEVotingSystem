/**
 * Reusable inline style getters for voter page content.
 * Each function takes the current theme and returns a React.CSSProperties object.
 * Use with useTheme() in page components.
 */

import type { Theme } from "../../styles/theme";

/** Link style (primary colour, underline) - for in-content links */
export const getLinkStyle = (theme: Theme) => ({
  color: theme.colors.secondary,
  textDecoration: "underline" as const,
});

/** Small icon (e.g. star) next to section headings - matches heading colour */
export const getSectionIconStyle = (theme: Theme) => ({
  display: "inline-block" as const,
  verticalAlign: "middle" as const,
  marginRight: theme.spacing.xs,
  fill: theme.colors.text.primary,
});

/** H3 with icon alignment - for subsections */
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

/** First content section (intro block) */
export const getFirstSectionStyle = (theme: Theme) => ({
  fontSize: theme.fontSizes.xl,
  color: theme.colors.text.secondary,
  lineHeight: 1.6,
  paddingLeft: theme.spacing.xl,
  paddingRight: theme.spacing.xl,
  paddingTop: theme.spacing.sm,
  paddingBottom: theme.spacing.md,
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

/** Section wrapper when it follows another section (reduces gap) */
export const getSectionWithPaddingStyle = (theme: Theme) => ({
  paddingTop: theme.spacing.md,
});

/** List (ul) inside page content */
export const getListStyle = (theme: Theme) => ({
  fontSize: theme.fontSizes.xl,
  color: theme.colors.text.secondary,
  lineHeight: 1.6,
  padding: theme.spacing.xl,
});

/** Centred content wrapper for voter pages – use with .voter-page-content class for responsive width */
export const getVoterPageContentWrapperStyle = (theme: Theme) => ({
  paddingLeft: theme.spacing.lg,
  paddingRight: theme.spacing.lg,
});

/** Card container (e.g. Before you start, Who can register) */
export const getRegistrationCardStyle = (theme: Theme) => ({
  backgroundColor: theme.colors.surface,
  border: `1px solid ${theme.colors.border}`,
  borderRadius: theme.borderRadius.lg,
  padding: theme.spacing.xl,
  boxShadow: theme.colors.shadows.sm,
});

/** Card title (h2) on registration page */
export const getRegistrationCardTitleStyle = (theme: Theme) => ({
  fontSize: theme.fontSizes.xl,
  fontWeight: theme.fontWeights.bold,
  color: theme.colors.text.primary,
  marginBottom: theme.spacing.md,
});

/** Card body text on registration page */
export const getRegistrationCardTextStyle = (theme: Theme) => ({
  fontSize: theme.fontSizes.base,
  color: theme.colors.text.secondary,
  lineHeight: 1.6,
  marginBottom: theme.spacing.sm,
});

/** List (ul) inside registration cards */
export const getRegistrationListStyle = (theme: Theme) => ({
  fontSize: theme.fontSizes.base,
  color: theme.colors.text.secondary,
  lineHeight: 1.8,
  paddingLeft: theme.spacing.xl,
  marginTop: theme.spacing.sm,
  marginBottom: theme.spacing.sm,
});
