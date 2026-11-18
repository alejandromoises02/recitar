import type { Venue } from "../../events/domain/venue";

const fold = (text: string) =>
  text
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .trim();

/**
 * The venues offered as chips: the `limit` with the most upcoming dates (ties by name), with the chosen
 * venues that are not among them first, so the filter in use is always in sight.
 */
export function venueChips(venues: Venue[], chosen: string[], limit: number): string[] {
  const top = [...venues]
    .sort((a, b) => b.upcomingEvents - a.upcomingEvents || a.name.localeCompare(b.name))
    .slice(0, limit)
    .map((venue) => venue.name);
  return [...chosen.filter((name) => !top.includes(name)), ...top];
}

/** The chosen venues with `venue` added (after the others) or, when it was chosen, removed. */
export function toggleVenue(chosen: string[], venue: string): string[] {
  return chosen.includes(venue) ? chosen.filter((name) => name !== venue) : [...chosen, venue];
}

/** Venues whose name holds `query`, ignoring case and accents, by name. */
export function matchingVenues(venues: Venue[], query: string): Venue[] {
  const wanted = fold(query);
  return venues.filter((venue) => fold(venue.name).includes(wanted)).sort((a, b) => a.name.localeCompare(b.name));
}
