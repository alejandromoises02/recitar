import { useCallback, useEffect, useMemo, useState } from "react";
import { configuredApiBase } from "../../../events/infrastructure/events-api";
import { useShows, useVenues } from "../../../events/infrastructure/events-queries";
import type { GroupBy } from "../../application/explore";
import { daysWithShows, groupShows, stripDays, whenRange } from "../../application/explore";
import { EXPLORE_PAGE_SIZE, GROUP_OPEN_MS, SEARCH_DEBOUNCE_MS, STRIP_QUERY_LIMIT } from "./explore.constants";
import { useDebouncedValue } from "./use-debounced-value";
import { useExploreFilters } from "./use-explore-filters";
import { useTrackFilters } from "./use-track-filters";
import { useLang } from "../../../../i18n/lang-context";

const NONE: ReadonlySet<string> = new Set();

/** Everything "Toda la cartelera" shows: filters, the listing pages, and the data for the filter panel. */
export function useExplore() {
  const lang = useLang();
  const [now] = useState(() => new Date());
  const [apiBase] = useState(configuredApiBase);
  const days = useMemo(() => stripDays(now, lang), [now, lang]);
  const filterState = useExploreFilters();
  const { filters } = filterState;
  useTrackFilters(filters);
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
  const groups = useMemo(() => groupShows(shows, filters.group, now, lang, range, horizon), [shows, filters.group, now, lang, range, horizon]);
  const visible = useMemo(() => groups.reduce((sum, group) => sum + group.count, 0), [groups]);
  const marked = useMemo(() => daysWithShows(strip.data?.pages[0].items ?? []), [strip.data]);
  const venueList = useMemo(() => venues.data ?? [], [venues.data]);

  // Collapsed groups belong to one "Ver por" choice: another choice makes other groups, all open.
  const [collapsedBy, setCollapsedBy] = useState<{ by: GroupBy; keys: ReadonlySet<string> }>(() => ({ by: filters.group, keys: new Set() }));
  const collapsed = collapsedBy.by === filters.group ? collapsedBy.keys : NONE;
  // The group just unfolded: only its rows fade in, so rows the list mounts while scrolling do not.
  const [opened, setOpened] = useState<string | null>(null);
  const toggleGroup = useCallback(
    (key: string) => {
      const opening = collapsed.has(key);
      setOpened(opening ? key : null);
      setCollapsedBy(() => {
        const keys = new Set(collapsed);
        if (opening) keys.delete(key);
        else keys.add(key);
        return { by: filters.group, keys };
      });
    },
    [collapsed, filters.group],
  );
  useEffect(() => {
    if (!opened) return;
    const timer = setTimeout(() => setOpened(null), GROUP_OPEN_MS);
    return () => clearTimeout(timer);
  }, [opened]);

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
    venues: venueList,
    groups,
    collapsed,
    opened,
    toggleGroup,
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
