import type { Event } from "../domain/event";
import { filterVisible } from "./visible-events";

export function pickFeatured(
  events: Event[],
  curatedIds: string[],
  now: Date,
  limit: number,
): Event[] {
  const upcoming = filterVisible(events).filter((e) => e.startsAt.getTime() >= now.getTime());
  const byId = new Map(upcoming.map((e) => [e.id, e]));

  const curated: Event[] = [];
  for (const id of curatedIds) {
    const event = byId.get(id);
    if (event && !curated.includes(event)) curated.push(event);
  }

  const soonest = upcoming
    .filter((e) => !curated.includes(e))
    .sort((x, y) => x.startsAt.getTime() - y.startsAt.getTime());

  return [...curated, ...soonest].slice(0, limit);
}
