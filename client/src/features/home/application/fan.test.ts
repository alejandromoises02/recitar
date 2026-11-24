import { describe, expect, it } from "vitest";
import { fanCardSize, fanLanding, fanOffset, fanPose, fanShift, fanSpread, tappedStep, tapsRecord } from "./fan";

describe("fanOffset", () => {
  it("is how many steps a sleeve sits from the centre", () => {
    expect(fanOffset(3, 1, 8)).toBe(2);
    expect(fanOffset(0, 1, 8)).toBe(-1);
  });

  it("wraps around, so the last sleeve sits left of the first", () => {
    expect(fanOffset(7, 0, 8)).toBe(-1);
    expect(fanOffset(0, 7, 8)).toBe(1);
  });

  it("follows an unbounded position past the end", () => {
    expect(fanOffset(1, 9, 8)).toBe(0);
  });

  it("is fractional while the fan is dragged", () => {
    expect(fanOffset(2, 1.25, 8)).toBeCloseTo(0.75);
  });
});

describe("fanPose", () => {
  it("keeps the centre sleeve straight, full size, bright and on top", () => {
    expect(fanPose(0, 100)).toEqual({ translateX: 0, translateY: 0, rotate: 0, scale: 1, zIndex: 90, visible: true, dim: 0 });
  });

  it("moves, drops, tilts, shrinks and dims a side sleeve", () => {
    const pose = fanPose(-2, 100);
    expect(pose.translateX).toBe(-200);
    expect(pose.translateY).toBe(28);
    expect(pose.rotate).toBe(-11);
    expect(pose.scale).toBeCloseTo(0.86);
    expect(pose.zIndex).toBe(70);
    expect(pose.visible).toBe(true);
    expect(pose.dim).toBeCloseTo(0.42);
  });

  it("hides sleeves past the visible steps", () => {
    expect(fanPose(3, 100).visible).toBe(false);
  });

  it("stops shrinking after three steps", () => {
    expect(fanPose(4, 100).scale).toBe(fanPose(3, 100).scale);
  });
});

describe("fanSpread", () => {
  it("is a fifth of the fan's width on narrow fans", () => {
    expect(fanSpread(540, 400)).toBe(100);
  });

  it("is never more than half a sleeve", () => {
    expect(fanSpread(2000, 300)).toBe(150);
  });
});

describe("fanCardSize", () => {
  it.each([
    [390, true, 218],
    [820, true, 250],
    [1000, false, 220],
    [1440, false, 274],
    [3000, false, 440],
  ])("a %i px screen (stacked %s) gets %i px sleeves", (screen, stacked, size) => {
    expect(fanCardSize(screen, stacked)).toBe(size);
  });
});

describe("fanShift", () => {
  it("is zero when the record fits beside the centre sleeve", () => {
    expect(fanShift(800, 200, 180)).toBe(0);
  });

  it("moves the fan left just enough to keep the record inside, with a small margin", () => {
    // record right edge: 179 + 144 + 70 = 393 on a 358 px fan -> 35 px over, plus the 4 px margin
    expect(fanShift(358, 144, 140)).toBe(39);
  });
});

describe("fanLanding", () => {
  // Positions are in sleeves; dragging the finger left moves the fan to the next show (higher position).
  it("moves one show on a short swipe past a fifth of a sleeve", () => {
    expect(fanLanding(3, 3.25, 0)).toBe(4);
    expect(fanLanding(3, 2.75, 0)).toBe(2);
  });

  it("stays on a tiny slow drag", () => {
    expect(fanLanding(3, 3.1, 0)).toBe(3);
  });

  it("moves one show on a quick flick even when the drag was tiny", () => {
    expect(fanLanding(3, 3.05, -800)).toBe(4);
    expect(fanLanding(3, 2.95, 800)).toBe(2);
  });

  it("follows the flick direction when it disagrees with the drag", () => {
    expect(fanLanding(3, 3.15, 800)).toBe(2);
  });

  it("moves several shows on a long drag", () => {
    expect(fanLanding(3, 5.4, 0)).toBe(5);
    expect(fanLanding(3, 5.4, -800)).toBe(5);
  });

  it("counts from the show that was centred when the drag began", () => {
    expect(fanLanding(3.4, 3.7, 0)).toBe(4);
  });
});

describe("tappedStep", () => {
  // Centre sleeve at x = 200, neighbours every 100 px.
  it("is 0 on the centre sleeve", () => {
    expect(tappedStep(230, 200, 100)).toBe(0);
  });

  it("is how many sleeves left or right of the centre the tap was", () => {
    expect(tappedStep(290, 200, 100)).toBe(1);
    expect(tappedStep(20, 200, 100)).toBe(-2);
  });
});

describe("tapsRecord", () => {
  // A record of 100 px whose centre is at (300, 200).
  it("is a tap inside the record's circle", () => {
    expect(tapsRecord(300, 200, 300, 200, 100)).toBe(true);
    expect(tapsRecord(340, 225, 300, 200, 100)).toBe(true);
  });

  it("is not a tap outside it, even inside its square corners", () => {
    expect(tapsRecord(351, 200, 300, 200, 100)).toBe(false);
    expect(tapsRecord(345, 245, 300, 200, 100)).toBe(false);
  });
});
