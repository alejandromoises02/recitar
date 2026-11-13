import { breakpoints } from "../../../design/tokens";

export type HomeSection = "featured" | "justAnnounced" | "next" | "explore";

export type HomeLayout =
  | { kind: "stacked"; order: HomeSection[] }
  | { kind: "split"; left: HomeSection; right: HomeSection; leftShare: number; below: HomeSection[] };

export function homeLayout(width: number): HomeLayout {
  if (width <= breakpoints.stacked) {
    return { kind: "stacked", order: ["featured", "justAnnounced", "next", "explore"] };
  }
  return { kind: "split", left: "justAnnounced", right: "featured", leftShare: 0.4, below: ["next", "explore"] };
}
