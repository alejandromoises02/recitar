import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { colors, motion, palette } from "./tokens";

// DESIGN.md (repo root) is the design source of truth; tokens.ts must carry the same colour values.
const designMd = readFileSync(new URL("../../../DESIGN.md", import.meta.url), "utf8");

function frontmatterColors(md: string): Record<string, string> {
  const front = md.split("---")[1] ?? "";
  const block = front.split(/\ncolors:\n/)[1]?.split(/\n\S/)[0] ?? "";
  return Object.fromEntries(
    [...block.matchAll(/^\s+([\w-]+):\s+"([^"]+)"/gm)].map(([, key, value]) => [key, value]),
  );
}

const kebab = (key: string) => key.replace(/[A-Z]/g, (c) => `-${c.toLowerCase()}`);

function channels(color: string): [number, number, number, number] {
  const hex = /^#([0-9a-f]{6})$/i.exec(color);
  if (hex) {
    const n = Number.parseInt(hex[1], 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255, 1];
  }
  const rgba = /^rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)$/.exec(color);
  if (!rgba) throw new Error(`Unsupported colour: ${color}`);
  return [Number(rgba[1]), Number(rgba[2]), Number(rgba[3]), Number(rgba[4])];
}

function over(fg: string, bg: string): [number, number, number] {
  const [r, g, b, a] = channels(fg);
  const [br, bgG, bb] = channels(bg);
  return [r * a + br * (1 - a), g * a + bgG * (1 - a), b * a + bb * (1 - a)];
}

function luminance([r, g, b]: [number, number, number]): number {
  const lin = (v: number) => {
    const s = v / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
}

function contrast(fg: string, bg: string): number {
  const a = luminance(over(fg, bg));
  const b = luminance(over(bg, "#000000"));
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}

describe("palette", () => {
  it("matches the colours in DESIGN.md frontmatter, one for one", () => {
    const fromDesign = frontmatterColors(designMd);
    const fromTokens = Object.fromEntries(Object.entries(palette).map(([k, v]) => [kebab(k), v]));
    expect(Object.keys(fromDesign).length).toBeGreaterThan(0);
    expect(fromTokens).toEqual(fromDesign);
  });
});

describe("colors", () => {
  it.each([
    ["text on background", colors.text, colors.background],
    ["muted text on background", colors.textMuted, colors.background],
    ["muted text on a flap cell", colors.textMuted, colors.flapTop],
    ["accent on background", colors.accent, colors.background],
    ["text on accent", colors.onAccent, colors.accent],
    ["text on the primary button", colors.onPrimary, colors.primary],
  ])("%s reaches WCAG AA (4.5:1)", (_, fg, bg) => {
    expect(contrast(fg, bg)).toBeGreaterThanOrEqual(4.5);
  });
});

describe("motion", () => {
  it("keeps every duration positive and every easing a valid cubic-bezier", () => {
    for (const ms of [...Object.values(motion.duration), ...Object.values(motion.signature)]) {
      expect(ms).toBeGreaterThan(0);
    }
    for (const [x1, , x2] of Object.values(motion.easing)) {
      expect(x1).toBeGreaterThanOrEqual(0);
      expect(x2).toBeLessThanOrEqual(1);
    }
  });
});
