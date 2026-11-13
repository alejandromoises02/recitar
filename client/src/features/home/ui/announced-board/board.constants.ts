import { Easing } from "react-native-reanimated";
import { motion, spacing } from "../../../../design/tokens";

export const PHONE_FLAP_SIZE = 19;
export const ROW_GAP = spacing.hair;
export const SKELETON_ROWS = 5;

/** Board geometry in em of the flap font size, per layout (DESIGN.md board). */
export const ROW_HEIGHT_EM = 2.6;
export const DATE_WIDTH_EM = { stacked: 5, split: 5.6 };
export const PHOTO_SHARE = { stacked: 0.3, split: 0.38 };
export const SUB_TEXT_EM = 0.7;
export const ERROR_HEIGHT_EM = 6;

export const FLIP = {
  firstDelay: 200,
  stagger: motion.signature.flapStagger,
  duration: motion.signature.flapFlip,
  easing: Easing.bezier(...motion.easing.smoothOut),
  perspective: 600,
  startAngle: -90,
};

export const PHOTO_FADE_STOP = "28%";

export type BoardGeometry = { flapSize: number; dateWidth: number; photoShare: number };
