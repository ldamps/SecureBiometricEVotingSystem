import type { Theme } from "../theme";

export const getTabsStyle = (theme: Theme) => ({
    paddingLeft: theme.spacing.xl,
    paddingRight: theme.spacing.xl,
    color: theme.colors.text.primary,
});
