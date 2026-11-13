import { spacing } from "../../../../design/tokens";
import { THUMB_SIZE } from "./ShowCard.constants";

export const CARD_GAP = spacing.sm;
export const PHONE_CARD_WIDTH = 250;
/** Wide screens show a cut fifth card, so the strip reads as scrollable. */
export const CARDS_PER_VIEW = 4.4;
export const PAGE_FRACTION = 0.9;
export const SKELETON_CARDS = { wide: 4, phone: 2 };
export const CARD_HEIGHT = THUMB_SIZE + 2 * spacing.xs + 2;
