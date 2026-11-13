import { Easing } from "react-native-reanimated";
import { motion } from "../../../../design/tokens";

export const FAN_HEIGHT_SHARE = 1.4;
export const EDGE_FADE_SHARE = "9%";
export const DRAG_ACTIVATION = 10;
export const SPOT_WIDTH_SHARE = 1.9;

export const SLEEVE_MOVE = { duration: motion.signature.sleeveMove, easing: Easing.bezier(...motion.easing.swap) };
export const RECORD_OUT = { duration: motion.signature.recordOut, easing: Easing.bezier(...motion.easing.smoothOut) };
export const RECORD_IN = { duration: motion.signature.recordIn, easing: Easing.bezier(...motion.easing.swap) };
/** The record slides out once the card text has swapped (mock: 280 ms swap + 380 ms). */
export const RECORD_OUT_DELAY = 660;
export const RECORD_HIDDEN_SCALE = 0.96;

export const AUTOPLAY_MS = motion.signature.carouselAutoplay;
export const CARD_SWAP_MS = motion.duration.fast;

/** Record parts as shares of the record size. */
export const RECORD_LABEL_SHARE = 0.36;
export const RECORD_HOLE_SHARE = 0.03;
export const RECORD_GROOVES = [0.62, 0.8];

export const SLEEVE_TITLE_SHARE = 0.085;
export const SLEEVE_VENUE_SHARE = 0.045;
export const CTA_ICON_SIZE = 38;
