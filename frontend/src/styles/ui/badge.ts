import type { Theme } from "../theme";

export const getBadgeStyle = (theme: Theme) => ({
    backgroundColor: theme.colors.badge,
    display: "inline-block",
    padding: theme.spacing.xs,
})