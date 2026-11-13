import { useCallback, useEffect, useMemo, useState } from "react";
import { configuredApiBase } from "../../../events/infrastructure/events-api";
import { useShows, useVenues } from "../../../events/infrastructure/events-queries";
import { daysWithShows, groupShows, stripDays, whenRange } from "../../application/explore";
import { EXPLORE_PAGE_SIZE, SEARCH_DEBOUNCE_MS, STRIP_QUERY_LIMIT } from "./explore.constants";
import { useDebouncedValue } from "./use-debounced-value";
import { useExploreFilters } from "./use-explore-filters";

/** Everything "Toda la cartelera" shows: filters, the listing pages, and the data for the filter panel. */
export function useExplore() {
  const [now] = useState(() => new Date());
  const [apiBase] = useState(configuredApiBase);
  const days = useMemo(() => stripDays(now), [now]);
  const filterState = useExploreFilters();
  const { filters } = filterState;
  const text = useDebouncedValue(filters.text.trim(), SEARCH_DEBOUNCE_MS);
  const range = useMemo(() => whenRange(filters.when, now, filters.day ?? undefined), [filters.when, filters.day, now]);

  const query = useMemo(
    () => ({ limit: EXPLORE_PAGE_SIZE, q: text, venue: filters.venue, from: range.from, to: range.to }),
    [text, filters.venue, range],
  );
  const listing = useShows(query);
  const [stripQuery] = useState(() => ({ from: days[0].iso, to: days[days.length - 1].iso, limit: STRIP_QUERY_LIMIT }));
  const strip = useShows(stripQuery);
  const venues = useVenues();

  const shows = useMemo(() => listing.data?.pages.flatMap((page) => page.items) ?? [], [listing.data]);
  const { hasNextPage, isFetchingNextPage, fetchNextPage, refetch } = listing;
  // Shows come by their next date, so later pages can still hold dates up to the last loaded show's.
  const horizon = hasNextPage && shows.length > 0 ? shows[shows.length - 1].dates[0].startsAt : null;
  const groups = useMemo(() => groupShows(shows, filters.group, now, range, horizon), [shows, filters.group, now, range, horizon]);
  const visible = useMemo(() => groups.reduce((sum, group) => sum + group.count, 0), [groups]);
  const marked = useMemo(() => daysWithShows(strip.data?.pages[0].items ?? []), [strip.data]);
  const venueNames = useMemo(() => venues.data?.map((venue) => venue.name) ?? [], [venues.data]);

  const fetchMore = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) fetchNextPage();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);
  const retry = useCallback(() => refetch(), [refetch]);

  // A page whose dates all fall past the horizon shows nothing yet: keep loading until something does.
  useEffect(() => {
    if (visible === 0 && hasNextPage && !isFetchingNextPage) fetchNextPage();
  }, [visible, hasNextPage, isFetchingNextPage, fetchNextPage]);

  return {
    ...filterState,
    apiBase,
    now,
    days,
    marked,
    venueNames,
    groups,
    count: shows.length,
    visible,
    loaded: listing.data !== undefined,
    hasNextPage,
    isPending: listing.isPending,
    isError: listing.isError,
    isFetchingNextPage,
    fetchMore,
    retry,
  };
}

export type Explore = ReturnType<typeof useExplore>;
