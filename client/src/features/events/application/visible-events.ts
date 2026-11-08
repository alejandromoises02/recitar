import type { Event, EventCategory } from "../domain/event";

/**
 * Categories the app shows. The server stores every kind of event; the client starts with
 * concerts only. Add "party", "theatre" or "other" here when they are ready to be shown.
 */
export const VISIBLE_CATEGORIES: EventCategory[] = ["concert"];

export function filterVisible(
  events: Event[],
  categories: EventCategory[] = VISIBLE_CATEGORIES,
): Event[] {
  return events.filter((e) => categories.includes(e.category));
}
