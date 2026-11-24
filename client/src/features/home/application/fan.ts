import { fan } from "../../../design/tokens";
import {
  CARD_SIZE,
  CENTRE_Z_INDEX,
  DROP_PER_STEP_SQUARED,
  FLICK_VELOCITY,
  MAX_SHRINK_STEPS,
  MAX_SPREAD_SHARE,
  RECORD_EDGE_MARGIN,
  SPREAD_DIVISOR,
  SWIPE_STEP_SHARE,
  Z_INDEX_PER_STEP,
} from "./fan.constants";

// fanOffset and fanPose run inside Reanimated worklets, so they carry the "worklet" directive.

export type FanPose = {
  translateX: number;
  translateY: number;
  rotate: number;
  scale: number;
  zIndex: number;
  visible: boolean;
  dim: number;
};

/** Steps from the centre for sleeve `index` when the fan sits at `position`, in (-count/2, count/2]. */
export function fanOffset(index: number, position: number, count: number): number {
  "worklet";
  let offset = (((index - position) % count) + count) % count;
  if (offset > count / 2) offset -= count;
  return offset;
}

export function fanPose(offset: number, spread: number): FanPose {
  "worklet";
  const steps = Math.abs(offset);
  return {
    translateX: offset * spread,
    translateY: steps * steps * DROP_PER_STEP_SQUARED,
    rotate: offset * fan.tiltPerStep,
    scale: 1 - Math.min(steps, MAX_SHRINK_STEPS) * fan.shrinkPerStep,
    zIndex: CENTRE_Z_INDEX - Math.round(steps * Z_INDEX_PER_STEP),
    visible: steps <= fan.visibleSteps,
    dim: Math.min(steps, 1) * (1 - fan.sideBrightness),
  };
}

/** Distance between neighbouring sleeves. */
export function fanSpread(fanWidth: number, cardSize: number): number {
  return Math.min(fanWidth / SPREAD_DIVISOR, cardSize * MAX_SPREAD_SHARE);
}

export function fanCardSize(screen: number, stacked: boolean): number {
  const size = stacked
    ? Math.min(screen * CARD_SIZE.stackedShare, CARD_SIZE.stackedMax)
    : Math.min(Math.max(screen * CARD_SIZE.splitShare, CARD_SIZE.splitMin), CARD_SIZE.splitMax);
  return Math.round(size);
}

/** How far to move the fan left so the record, `travel` right of the centre, stays inside it. */
export function fanShift(fanWidth: number, travel: number, recordSize: number): number {
  return Math.max(0, travel + recordSize / 2 + RECORD_EDGE_MARGIN - fanWidth / 2);
}

/**
 * Where a drag lands, in sleeves. `start` is the position when the finger went down, `position`
 * where it is now, `velocityX` the finger speed (negative = leftwards = next show).
 */
export function fanLanding(start: number, position: number, velocityX: number): number {
  "worklet";
  const base = Math.round(start);
  const moved = position - base;
  const distance = Math.max(1, Math.round(Math.abs(moved)));
  if (Math.abs(velocityX) > FLICK_VELOCITY) {
    const direction = velocityX < 0 ? 1 : -1;
    return base + direction * (Math.sign(moved) === direction ? distance : 1);
  }
  if (Math.abs(moved) < SWIPE_STEP_SHARE) return base;
  return base + Math.sign(moved) * distance;
}

/** Which sleeve a tap at `x` hit, in steps from the centre sleeve at `centreX`. */
export function tappedStep(x: number, centreX: number, spread: number): number {
  "worklet";
  return Math.round((x - centreX) / spread);
}

/** Whether a tap at (`x`, `y`) fell on the record of `size` centred at (`recordX`, `recordY`): it is round. */
export function tapsRecord(x: number, y: number, recordX: number, recordY: number, size: number): boolean {
  "worklet";
  return Math.hypot(x - recordX, y - recordY) <= size / 2;
}
