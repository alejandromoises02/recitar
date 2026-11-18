import type { FilterUse, NoResultsUse } from "../../analytics/tracker";
import type { GroupBy, When } from "./explore";

export type FilterState = { text: string; venues: string[]; when: When; day: string | null; group: GroupBy };

/** The longest venue text the API keeps on an analytics event. */
const VENUE_TEXT_MAX = 120;

/**
 * Which filter the visitor just used, if any. Only choosing counts: clearing a filter does not, and the search
 * counts once, when it starts, and never carries what was typed.
 */
export function filterUsed(before: FilterState, after: FilterState): FilterUse | null {
  if (before.text === "" && after.text !== "") return { filter: "search" };
  const added = after.venues.find((venue) => !before.venues.includes(venue));
  if (added !== undefined) return { filter: "venue", value: added };
  if (after.when === "day" && after.day !== null && after.day !== before.day) return { filter: "day", value: after.day };
  if (after.when !== "all" && after.when !== "day" && after.when !== before.when) return { filter: "when", value: after.when };
  if (after.group !== before.group) return { filter: "group", value: after.group };
  return null;
}

/**
 * What was asked for when the listing came back empty, or null when no filter was on (then an empty listing says
 * nothing about what people look for). The search only counts as on, never with what was typed.
 */
export function noResults(state: FilterState): NoResultsUse | null {
  const filters: NoResultsUse["filters"] = [];
  const use: NoResultsUse = { filters };
  if (state.text.trim() !== "") filters.push("search");
  if (state.venues.length > 0) {
    filters.push("venue");
    use.venue = state.venues.join(", ").slice(0, VENUE_TEXT_MAX);
  }
  if (state.when === "day" && state.day !== null) {
    filters.push("day");
    use.when = state.day;
  } else if (state.when !== "all" && state.when !== "day") {
    filters.push("when");
    use.when = state.when;
  }
  return filters.length > 0 ? use : null;
}
