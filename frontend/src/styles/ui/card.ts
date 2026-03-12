/**
 * Reusable card styles – container, title, body text, list inside cards.
 */

import type { Theme } from "../theme";

/** Card container (e.g. Before you start, Who can register, login cards) */
export const getCardStyle = (theme: Theme) => ({
  backgroundColor: theme.colors.surface,
  border: `1px solid ${theme.colors.border}`,
  borderRadius: theme.borderRadius.lg,
  padding: theme.spacing.xl,
  boxShadow: theme.colors.shadows.sm,
});

/** Card title (h2) */
export const getCardTitleStyle = (theme: Theme) => ({
  fontSize: theme.fontSizes.xl,
  fontWeight: theme.fontWeights.bold,
  color: theme.colors.text.primary,
  marginBottom: theme.spacing.md,
});

/** Card body text */
export const getCardTextStyle = (theme: Theme) => ({
  fontSize: theme.fontSizes.base,
  color: theme.colors.text.secondary,
  lineHeight: 1.6,
  marginBottom: theme.spacing.sm,
});

/** List (ul) inside cards */
export const getCardListStyle = (theme: Theme) => ({
  fontSize: theme.fontSizes.base,
  color: theme.colors.text.secondary,
  lineHeight: 1.8,
  paddingLeft: theme.spacing.xl,
  marginTop: theme.spacing.sm,
  marginBottom: theme.spacing.sm,
});
