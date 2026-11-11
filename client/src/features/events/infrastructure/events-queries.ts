import { infiniteQueryOptions, queryOptions, useInfiniteQuery, useQuery } from "@tanstack/react-query";
import type { EventsApi, EventsQuery } from "./events-api";
import { eventsApi } from "./events-api";

/** What GET /events can filter by; the cursor is handled by the query. */
export type EventFilters = Omit<EventsQuery, "cursor" | "limit">;

/** Empty filters ask for the same events as no filter, so they share its cache entry. Key order
 * needs no care: TanStack Query hashes object keys sorted. */
function withoutEmpty<T extends object>(value: T): T {
  return Object.fromEntries(Object.entries(value).filter(([, v]) => v !== undefined && v !== null && v !== "")) as T;
}

export const eventKeys = {
  all: ["events"] as const,
  list: (filters: EventFilters) => ["events", "list", withoutEmpty(filters)] as const,
  detail: (id: string) => ["events", "detail", id] as const,
  venues: ["venues"] as const,
};

/** Upcoming events, a page at a time: each next page is asked for with the previous next_cursor. */
export function eventsQueryOptions(api: EventsApi, filters: EventFilters = {}) {
  return infiniteQueryOptions({
    queryKey: eventKeys.list(filters),
    queryFn: ({ pageParam }) => api.listEvents({ ...filters, cursor: pageParam }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (last) => last.nextCursor ?? undefined,
  });
}

export function eventQueryOptions(api: EventsApi, id: string) {
  return queryOptions({ queryKey: eventKeys.detail(id), queryFn: () => api.getEvent(id) });
}

export function venuesQueryOptions(api: EventsApi) {
  return queryOptions({ queryKey: eventKeys.venues, queryFn: () => api.listVenues() });
}

export const useEvents = (filters: EventFilters = {}) => useInfiniteQuery(eventsQueryOptions(eventsApi(), filters));
export const useEvent = (id: string) => useQuery(eventQueryOptions(eventsApi(), id));
export const useVenues = () => useQuery(venuesQueryOptions(eventsApi()));
