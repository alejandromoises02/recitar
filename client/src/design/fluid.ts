/** Screen widths where a fluid size reaches its minimum and its maximum (DESIGN.md clamp() ranges). */
export const FLUID_MIN_WIDTH = 390;
export const FLUID_MAX_WIDTH = 1280;

/** A size from a { min, max } token for a screen `width` wide: linear in between, whole points. */
export function fluid(size: { min: number; max: number }, width: number): number {
  const t = Math.min(1, Math.max(0, (width - FLUID_MIN_WIDTH) / (FLUID_MAX_WIDTH - FLUID_MIN_WIDTH)));
  return Math.round(size.min + (size.max - size.min) * t);
}
