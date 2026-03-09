/**
 * Reusable section and layout styles – first section, section padding, icon, page wrapper.
 */

import type { Theme } from "../theme";

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

/** Section wrapper when it follows another section (reduces gap) */
export const getSectionWithPaddingStyle = (theme: Theme) => ({
  paddingTop: theme.spacing.md,
});

/** Small icon next to section headings – matches heading colour */
export const getSectionIconStyle = (theme: Theme) => ({
  display: "inline-block" as const,
  verticalAlign: "middle" as const,
  marginRight: theme.spacing.xs,
  fill: theme.colors.text.primary,
});

/** Content wrapper for voter/content pages – use with .voter-page-content class for responsive width */
export const getPageContentWrapperStyle = (theme: Theme) => ({
  paddingLeft: theme.spacing.lg,
  paddingRight: theme.spacing.lg,
});
