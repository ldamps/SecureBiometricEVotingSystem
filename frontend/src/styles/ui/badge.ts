import type { Theme } from "../theme";

export const getBadgeStyle = (theme: Theme) => ({
  backgroundColor: theme.colors.badge,
  display: "inline-block",
  padding: theme.spacing.xs,
});

export type StatusBadgeVariant = "ok" | "mismatch" | "pending" | "open" | "in_progress" | "resolved";

export const getStatusBadgeStyle = (theme: Theme, variant: StatusBadgeVariant) => {
  const colors: Record<StatusBadgeVariant, string> = {
    ok: theme.colors.status.success,
    mismatch: theme.colors.status.error,
    pending: theme.colors.status.warning,
    open: theme.colors.status.warning,
    in_progress: theme.colors.status.info,
    resolved: theme.colors.status.success,
  };
  const color = colors[variant];
  // Use higher alpha on dark backgrounds for better contrast
  const isDark = theme.colors.background === "#0A1228";
  const bgAlpha = isDark ? "33" : "22";
  return {
    padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
    borderRadius: theme.borderRadius.full,
    fontSize: theme.fontSizes.xs,
    fontWeight: theme.fontWeights.medium,
    backgroundColor: color + bgAlpha,
    color,
  };
};