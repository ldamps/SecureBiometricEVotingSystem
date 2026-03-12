/**
 * Reusable link styles – in-content links.
 */

import type { Theme } from "../theme";

/** Link style (primary colour, underline) – for in-content links */
export const getLinkStyle = (theme: Theme) => ({
  color: theme.colors.secondary,
  textDecoration: "underline" as const,
});
