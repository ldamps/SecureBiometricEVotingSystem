import type { Theme } from "../theme";

export const getSuccessAlertStyle = (theme: Theme) => ({
  padding: theme.spacing.md,
  borderRadius: theme.borderRadius?.md || "8px",
  backgroundColor: theme.colors.status.success + "18",
  border: `1px solid ${theme.colors.status.success}`,
  color: theme.colors.text.primary,
});

export const getErrorAlertStyle = (theme: Theme) => ({
  padding: theme.spacing.md,
  borderRadius: theme.borderRadius?.md || "8px",
  backgroundColor: theme.colors.status.error + "18",
  border: `1px solid ${theme.colors.status.error}`,
  color: theme.colors.text.primary,
});
