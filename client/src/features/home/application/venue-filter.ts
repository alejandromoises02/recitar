import type { Venue } from "../../events/domain/venue";

const fold = (text: string) =>
  text
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .trim();

/**
 * The venues offered as chips: the `limit` with the most upcoming dates (ties by name), with the chosen
 * venue first when it is not among them, so the filter in use is always in sight.
 */
export function venueChips(venues: Venue[], chosen: string | null, limit: number): string[] {
  const top = [...venues]
    .sort((a, b) => b.upcomingEvents - a.upcomingEvents || a.name.localeCompare(b.name))
    .slice(0, limit)
    .map((venue) => venue.name);
  return chosen !== null && !top.includes(chosen) ? [chosen, ...top] : top;
}

/** Venues whose name holds `query`, ignoring case and accents, by name. */
export function matchingVenues(venues: Venue[], query: string): Venue[] {
  const wanted = fold(query);
  return venues.filter((venue) => fold(venue.name).includes(wanted)).sort((a, b) => a.name.localeCompare(b.name));
}
