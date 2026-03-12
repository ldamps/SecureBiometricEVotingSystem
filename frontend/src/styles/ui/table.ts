import type { Theme } from "../theme";

export const getTableStyle = (theme: Theme) => ({
  width: "100%" as const,
  borderCollapse: "collapse" as const,
  fontSize: theme.fontSizes.sm,
});

export const getTableHeaderStyle = (theme: Theme) => ({
  textAlign: "left" as const,
  padding: theme.spacing.sm,
  borderBottom: `2px solid ${theme.colors.border}`,
  color: theme.colors.text.secondary,
  fontWeight: theme.fontWeights.semibold,
});

export const getTableCellStyle = (theme: Theme) => ({
  padding: theme.spacing.sm,
  borderBottom: `1px solid ${theme.colors.border}`,
  color: theme.colors.text.primary,
});
