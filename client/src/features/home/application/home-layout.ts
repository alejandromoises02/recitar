import { breakpoints } from "../../../design/tokens";

export type HomeSection = "featured" | "justAnnounced" | "next" | "explore";

export type HomeLayout =
  | { kind: "stacked"; order: HomeSection[] }
  | { kind: "split"; left: HomeSection; right: HomeSection; leftShare: number; below: HomeSection[] };

/** Which sections go where for a screen `width` wide (home brief, "Chosen design"). Up to the
 * stacked breakpoint the hero is one column with Featured first; wider, Just announced (40%) sits
 * beside Featured (60%). */
export function homeLayout(width: number): HomeLayout {
  if (width <= breakpoints.stacked) {
    return { kind: "stacked", order: ["featured", "justAnnounced", "next", "explore"] };
  }
  return { kind: "split", left: "justAnnounced", right: "featured", leftShare: 0.4, below: ["next", "explore"] };
}
