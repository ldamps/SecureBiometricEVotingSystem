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

export {
  getStepTitleStyle,
  getStepDescStyle,
  getStepFormInputStyle,
  getStepLabelStyle,
} from "./step";

// Legacy aliases for backward compatibility (registration card = card, voter page wrapper = page content wrapper)
export {
  getCardStyle as getRegistrationCardStyle,
  getCardTitleStyle as getRegistrationCardTitleStyle,
  getCardTextStyle as getRegistrationCardTextStyle,
  getCardListStyle as getRegistrationListStyle,
} from "./card";
export { getPageContentWrapperStyle as getVoterPageContentWrapperStyle } from "./section";
