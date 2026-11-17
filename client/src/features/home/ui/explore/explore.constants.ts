import { Easing } from "react-native-reanimated";
import { motion, touchTarget } from "../../../../design/tokens";

export const EXPLORE_PAGE_SIZE = 50;
/** The API's largest page: enough to mark which of the next 14 days have shows. */
export const STRIP_QUERY_LIMIT = 100;
export const SEARCH_DEBOUNCE_MS = 300;
export const BLOCK_MIN_WIDTH = 340;
export const BLOCK_GAP = 12;
export const AGENDA_THUMB = 52;
export const DATE_COLUMN_WIDTH = 56;
export const GROUP_TITLE_SIZE = 18;
export const DAY_WIDTH = 58;
export const DAY_GAP = 6;
export const SKELETON_HEIGHT = 140;
export const ERROR_MIN_HEIGHT = 120;
export const CARD_MIN_WIDTH = 230;
export const CARD_GAP = 16;
export const CARD_IMAGE_RATIO = 4 / 3;
export const CALENDAR_CELL = touchTarget;
export const CALENDAR_MAX_WIDTH = 380;
export const CLOSE_SIZE = 36;
/** Venues offered as chips; the rest are one search away in the venue picker. */
export const VENUE_CHIPS = 8;
export const VENUE_PICKER_MAX_WIDTH = 460;
/** The picker leaves the page in sight above and below it. */
export const VENUE_PICKER_MAX_HEIGHT = "80%" as const;
export const MIN_TARGET = touchTarget;
/** A collapsed group's chevron points right. */
export const CHEVRON_TURN = { collapsed: -90, timing: { duration: motion.duration.fast, easing: Easing.bezier(...motion.easing.smoothOut) } };
/** How long rows of a just-unfolded group fade in when mounted; after it, rows mount without fading. */
export const GROUP_OPEN_MS = motion.duration.slow;
export const GROUP_FADE_MS = motion.duration.fast;
/** Rows below a folded or unfolded group slide to their new place. */
export const ROW_SHIFT_MS = motion.duration.fast;
/** The phone filter sheet never covers the whole screen, so the list stays in sight behind it. */
export const SHEET_MAX_HEIGHT = "85%" as const;
