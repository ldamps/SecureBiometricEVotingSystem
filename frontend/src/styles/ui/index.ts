/**
 * Reusable UI style getters. Each function takes the current theme and returns React.CSSProperties.
 * Use with useTheme() in components.
 *
 * Import from "@/styles/ui" or "../styles/ui" (depending on your path).
 */

export {
  getCardStyle,
  getCardTitleStyle,
  getCardTextStyle,
  getCardListStyle,
} from "./card";

export {
  getPageTitleStyle,
  getSectionH2Style,
  getH3Style,
  getPAfterHeaderStyle,
} from "./headers";

export { getLinkStyle } from "./links";

export {
  getFirstSectionStyle,
  getSectionWithPaddingStyle,
  getSectionIconStyle,
  getPageContentWrapperStyle,
} from "./section";

export { getListStyle } from "./list";

export { getBadgeStyle, getStatusBadgeStyle } from "./badge";
export type { StatusBadgeVariant } from "./badge";

export { getTabsStyle, getTabsContainerStyle, getTabButtonStyle } from "./tabs";

export { getTableStyle, getTableHeaderStyle, getTableCellStyle } from "./table";

export { getSelectorStyle, getSelectStyle } from "./selector";

export {
  getStepTitleStyle,
  getStepDescStyle,
  getStepFormInputStyle,
  getStepLabelStyle,
} from "./step";

export {
  getPrimaryButtonStyle,
  getPrimaryButtonHoverStyle,
  getSecondaryButtonStyle,
  getSecondaryButtonHoverStyle,
} from "./button";
export type { ButtonProps } from "./button";
export { PrimaryButton, SecondaryButton } from "./buttons";

// Legacy aliases for backward compatibility (registration card = card, voter page wrapper = page content wrapper)
export {
  getCardStyle as getRegistrationCardStyle,
  getCardTitleStyle as getRegistrationCardTitleStyle,
  getCardTextStyle as getRegistrationCardTextStyle,
  getCardListStyle as getRegistrationListStyle,
} from "./card";
export { getPageContentWrapperStyle as getVoterPageContentWrapperStyle } from "./section";
