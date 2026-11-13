/** Fan geometry from the mock, beside the DESIGN.md values in tokens.fan. */
export const SPREAD_DIVISOR = 5.4;
export const MAX_SPREAD_SHARE = 0.5;
export const DROP_PER_STEP_SQUARED = 7;
export const MAX_SHRINK_STEPS = 3;
export const CENTRE_Z_INDEX = 90;
export const Z_INDEX_PER_STEP = 10;

export const CARD_SIZE = {
  stackedShare: 0.56,
  stackedMax: 250,
  splitShare: 0.19,
  splitMin: 220,
  splitMax: 440,
};

/** Space kept between the slid-out record and the fan's right edge. */
export const RECORD_EDGE_MARGIN = 4;

/** A drag past this share of a sleeve moves to the neighbour. */
export const SWIPE_STEP_SHARE = 0.2;
/** A finger faster than this (points per second) is a flick: it moves one show its way. */
export const FLICK_VELOCITY = 500;
