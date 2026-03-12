/**
 * Reusable list styles – lists in page content.
 */

import type { Theme } from "../theme";

/** List (ul) inside page content */
export const getListStyle = (theme: Theme) => ({
  fontSize: theme.fontSizes.xl,
  color: theme.colors.text.secondary,
  lineHeight: 1.6,
  padding: theme.spacing.xl,
});
