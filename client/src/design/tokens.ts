// Design tokens for recitAR. Source of truth: DESIGN.md at the repo root ("The Night Marquee").
// tokens.test.ts fails if `palette` drifts from the DESIGN.md frontmatter colours.

/** Raw palette, one entry per DESIGN.md frontmatter colour (camelCase of its key). */
export const palette = {
  nightInk: "#0E0D0C",
  marqueeCream: "#F4EEDF",
  creamMuted: "rgba(244, 238, 223, 0.6)",
  hairline: "rgba(244, 238, 223, 0.12)",
  glass: "rgba(255, 255, 255, 0.04)",
  marqueeYellow: "#F2C230",
  fileteRed: "#B3241B",
  fileteBlue: "#2E6FBF",
  flapTop: "#25221F",
  flapBottom: "#1B1917",
  flapHinge: "#0A0908",
  cardSmoke: "rgba(18, 17, 16, 0.72)",
  sleeveEmpty: "#1C1A18",
} as const;

/** Semantic roles. Components use these, not the raw palette. */
export const colors = {
  background: palette.nightInk,
  text: palette.marqueeCream,
  textMuted: palette.creamMuted,
  line: palette.hairline,
  surface: palette.glass,
  card: palette.cardSmoke,
  accent: palette.marqueeYellow,
  onAccent: palette.nightInk,
  primary: palette.marqueeCream,
  onPrimary: palette.nightInk,
  brandShadowRed: palette.fileteRed,
  brandShadowBlue: palette.fileteBlue,
  alert: palette.fileteRed,
  flapTop: palette.flapTop,
  flapBottom: palette.flapBottom,
  flapHinge: palette.flapHinge,
  imageFallback: palette.sleeveEmpty,
} as const;

/**
 * Font families, one per weight: on React Native each loaded weight is its own family, and adding
 * fontWeight to a custom family can fake a bold on Android, so typography sets no fontWeight.
 * The names are the ones the @expo-google-fonts packages export; design/fonts.ts loads exactly these.
 */
export const fontFamily = {
  logo: "AlfaSlabOne_400Regular",
  display: "Unbounded_600SemiBold",
  displayMedium: "Unbounded_500Medium",
  body: "Onest_400Regular",
  bodyStrong: "Onest_600SemiBold",
  board: "BarlowCondensed_700Bold",
} as const;

export type FontName = (typeof fontFamily)[keyof typeof fontFamily];

/** Type roles. Fluid sizes from DESIGN.md are given as min / max in px; see design/fluid.ts. */
export const typography = {
  logo: { fontFamily: fontFamily.logo, size: { min: 24, max: 30 }, lineHeight: 1 },
  display: { fontFamily: fontFamily.display, size: { min: 30, max: 72 }, lineHeight: 1, letterSpacing: -0.035 },
  headline: { fontFamily: fontFamily.displayMedium, size: { min: 22, max: 36 }, lineHeight: 1.1, letterSpacing: -0.02 },
  body: { fontFamily: fontFamily.body, size: { min: 15, max: 15 }, lineHeight: 1.45 },
  bodySmall: { fontFamily: fontFamily.body, size: { min: 13, max: 13 }, lineHeight: 1.45 },
  label: { fontFamily: fontFamily.bodyStrong, size: { min: 11, max: 11 }, lineHeight: 1.3, letterSpacing: 0.16, uppercase: true },
  board: { fontFamily: fontFamily.board, size: { min: 17, max: 26 }, lineHeight: 1.1, letterSpacing: 0.06, uppercase: true, tabularNums: true },
} as const;

/** Letter spacing in DESIGN.md is in em; React Native wants points. */
export const tracking = (em: number, fontSize: number) => em * fontSize;

/** The logo's stepped shadow, as offsets in em: red, then an ink gap, then blue. */
export const brandShadow = [
  { offset: 0.06, color: palette.fileteRed },
  { offset: 0.12, color: palette.nightInk },
  { offset: 0.15, color: palette.fileteBlue },
] as const;

export const radius = { sleeve: 3, flap: 4, thumb: 9, cardSmall: 14, card: 18, pill: 999 } as const;

export const spacing = { hair: 4, xs: 8, sm: 12, md: 16, lg: 24, xl: 32, xxl: 48, xxxl: 64 } as const;

/** Layout breakpoints in px: at and below `stacked` the hero is one column. */
export const breakpoints = { stacked: 900, boardVenueHidden: 1100 } as const;

/**
 * Motion tokens for Reanimated. `duration` and `easing` follow the transitions.dev scale
 * (.claude/skills/transitions-polish/_root.css); `signature` holds the home's own moments from DESIGN.md.
 * Easings are cubic-bezier control points: use Easing.bezier(...points).
 */
export const motion = {
  duration: { stagger: 40, micro: 80, quick: 150, fast: 250, medium: 350, slow: 400, verySlow: 500 },
  easing: {
    smoothOut: [0.22, 1, 0.36, 1],
    inOut: [0.42, 0, 0.58, 1],
    out: [0, 0, 0.58, 1],
    swap: [0.65, 0, 0.25, 1],
  },
  distance: { micro: 4, small: 6, base: 8, medium: 12, large: 30 },
  scale: { large: 0.96, medium: 0.97, small: 0.98, tiny: 0.99, press: 0.97 },
  signature: {
    sleeveMove: 850, // fan reshuffle, easing.swap
    recordOut: 900, // record slides out, easing.smoothOut
    recordIn: 750, // record slides back, easing.swap
    recordTurn: 1800, // one turn at 33 rpm, linear, only while a sample plays
    flapFlip: 500, // board row flips in, easing.smoothOut
    flapStagger: 70,
    carouselAutoplay: 7000,
    livePulse: 2400,
  },
} as const;

/** Dims the page behind a dialog. */
export const scrim = "rgba(0, 0, 0, 0.6)";

/** The vinyl record drawn in the featured fan (mock values, not part of the DESIGN.md palette). */
export const recordColors = {
  vinyl: "#121214",
  groove: "rgba(255, 255, 255, 0.06)",
  rim: "#0B0B0C",
  sheen: "rgba(255, 255, 255, 0.14)",
  shadow: "rgba(0, 0, 0, 0.9)",
} as const;

/** Record fan geometry from DESIGN.md, as fractions of the sleeve size or per step from the centre. */
export const fan = {
  recordSize: 0.64,
  recordOut: 0.72,
  recordOutStacked: 0.66,
  tiltPerStep: 5.5,
  shrinkPerStep: 0.07,
  sideBrightness: 0.58,
  visibleSteps: 2.6,
} as const;
