import { describe, expect, it } from "vitest";
import { breakpoints } from "../../../design/tokens";
import { homeLayout } from "./home-layout";

describe("homeLayout", () => {
  it("stacks the sections on phones and tablets, featured first", () => {
    expect(homeLayout(390)).toEqual({ kind: "stacked", order: ["featured", "justAnnounced", "next", "explore"] });
    expect(homeLayout(breakpoints.stacked)).toEqual(homeLayout(390));
  });

  it("puts just announced (40%) beside featured (60%) on wide screens, the rest below", () => {
    expect(homeLayout(breakpoints.stacked + 1)).toEqual({
      kind: "split",
      left: "justAnnounced",
      right: "featured",
      leftShare: 0.4,
      below: ["next", "explore"],
    });
  });
});
