import type { Theme } from "../theme";

export const getTabsStyle = (theme: Theme) => ({
  paddingLeft: theme.spacing.xl,
  paddingRight: theme.spacing.xl,
  color: theme.colors.text.primary,
});

export const getTabsContainerStyle = (theme: Theme) => ({
  display: "flex" as const,
  gap: theme.spacing.sm,
  paddingLeft: theme.spacing.xl,
  paddingRight: theme.spacing.xl,
  paddingTop: theme.spacing.md,
  paddingBottom: theme.spacing.sm,
  borderBottom: `1px solid ${theme.colors.border}`,
  flexWrap: "wrap" as const,
});

export const getTabButtonStyle = (theme: Theme, active: boolean) => ({
  padding: `${theme.spacing.sm} ${theme.spacing.md}`,
  border: "none",
  borderRadius: theme.borderRadius.md,
  background: active ? theme.colors.primary : "transparent",
  color: active ? theme.colors.text.inverse : theme.colors.text.primary,
  fontWeight: theme.fontWeights.medium,
  cursor: "pointer",
  fontSize: theme.fontSizes.base,
});
