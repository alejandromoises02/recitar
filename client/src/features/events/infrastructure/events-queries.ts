import { infiniteQueryOptions, queryOptions, useInfiniteQuery, useQuery } from "@tanstack/react-query";
import type { EventsApi, EventsQuery, ShowsQuery } from "./events-api";
import { eventsApi } from "./events-api";

/** What GET /events can filter by; the cursor is handled by the query. */
export type EventFilters = Omit<EventsQuery, "cursor" | "limit">;

/** Empty filters ask for the same events as no filter, so they share its cache entry. Key order
 * needs no care: TanStack Query hashes object keys sorted. */
function withoutEmpty<T extends object>(value: T): T {
  return Object.fromEntries(Object.entries(value).filter(([, v]) => v !== undefined && v !== null && v !== "")) as T;
}

/** What GET /shows can filter and sort by; the cursor is handled by the query. */
export type ShowFilters = Omit<ShowsQuery, "cursor">;

export const eventKeys = {
  all: ["events"] as const,
  list: (filters: EventFilters) => ["events", "list", withoutEmpty(filters)] as const,
  detail: (id: string) => ["events", "detail", id] as const,
  venues: ["venues"] as const,
  shows: (filters: ShowFilters) => ["shows", "list", withoutEmpty(filters)] as const,
  featured: ["featured"] as const,
  show: (id: string) => ["shows", "detail", id] as const,
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

/** Upcoming shows, a page at a time, like eventsQueryOptions. */
export function showsQueryOptions(api: EventsApi, filters: ShowFilters = {}) {
  return infiniteQueryOptions({
    queryKey: eventKeys.shows(filters),
    queryFn: ({ pageParam }) => api.listShows({ ...filters, cursor: pageParam }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (last) => last.nextCursor ?? undefined,
  });
}

/** One show for its page; null when it does not exist. */
export function showQueryOptions(api: EventsApi, id: string) {
  return queryOptions({ queryKey: eventKeys.show(id), queryFn: () => api.getShow(id) });
}

export function featuredQueryOptions(api: EventsApi) {
  return queryOptions({ queryKey: eventKeys.featured, queryFn: () => api.getFeatured() });
}

export const useEvents = (filters: EventFilters = {}) => useInfiniteQuery(eventsQueryOptions(eventsApi(), filters));
export const useEvent = (id: string) => useQuery(eventQueryOptions(eventsApi(), id));
export const useVenues = () => useQuery(venuesQueryOptions(eventsApi()));
export const useShows = (filters: ShowFilters = {}) => useInfiniteQuery(showsQueryOptions(eventsApi(), filters));
export const useFeatured = () => useQuery(featuredQueryOptions(eventsApi()));
export const useShow = (id: string) => useQuery(showQueryOptions(eventsApi(), id));
