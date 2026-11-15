/** At and below this width the page is one column and the ticket button is pinned at the bottom. */
export const ONE_COLUMN_WIDTH = 900;
/** The poster takes the photo's shape between portrait 3:4 and landscape 4:3. */
export const POSTER_RATIO = { min: 3 / 4, max: 4 / 3, fallback: 3 / 4 } as const;
/** On phones the poster is never taller than wide, so the dates stay near the top. */
export const POSTER_MIN_RATIO_ONE_COLUMN = 1;
/** Beside the info the poster stops growing at this height, unless the info is taller; a taller photo is shown whole over its blurred copy. */
export const POSTER_MAX_HEIGHT_TWO_COLUMNS = 600;
export const TINT_HEIGHT = 640;
export const TILE_WIDTH = 68;
export const NAME_MAX_SIZE = 76;
export const NAME_MIN_SIZE = 30;
export const PINNED_BAR_HEIGHT = 84;
