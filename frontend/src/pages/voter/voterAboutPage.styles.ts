import type { Theme } from "../../styles/theme";

export const getLinkStyle = (theme: Theme) => ({
    color: theme.colors.secondary,
    textDecoration: "underline" as const,
});

export const getSectionStarStyle = (theme: Theme) => ({
    display: "inline-block" as const,
    verticalAlign: "middle" as const,
    marginRight: theme.spacing.xs,
    fill: theme.colors.text.primary,
});

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

export const getPAfterHeaderStyle = (theme: Theme) => ({
    fontSize: theme.fontSizes.xl,
    color: theme.colors.text.secondary,
    lineHeight: 1.6,
    paddingLeft: theme.spacing.xl,
    paddingRight: theme.spacing.xl,
    paddingTop: theme.spacing.xs,
    paddingBottom: theme.spacing.md,
});

export const getHeaderH1Style = (theme: Theme) => ({
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

export const getFirstSectionStyle = (theme: Theme) => ({
    fontSize: theme.fontSizes.xl,
    color: theme.colors.text.secondary,
    lineHeight: 1.6,
    paddingLeft: theme.spacing.xl,
    paddingRight: theme.spacing.xl,
    paddingTop: theme.spacing.sm,
    paddingBottom: theme.spacing.md,
});

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

export const getSectionWithPaddingStyle = (theme: Theme) => ({
    paddingTop: theme.spacing.md,
});

export const getListStyle = (theme: Theme) => ({
    fontSize: theme.fontSizes.xl,
    color: theme.colors.text.secondary,
    lineHeight: 1.6,
    padding: theme.spacing.xl,
});
