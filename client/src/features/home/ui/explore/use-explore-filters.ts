import { useCallback, useState } from "react";
import type { GroupBy, When } from "../../application/explore";
import { activeFilterCount } from "../../application/explore";
import { toggleVenue as toggled } from "../../application/venue-filter";

export type ExploreFilters = { text: string; venues: string[]; when: When; day: string | null; group: GroupBy };

const INITIAL: ExploreFilters = { text: "", venues: [], when: "all", day: null, group: "day" };

export function useExploreFilters() {
  const [filters, setFilters] = useState(INITIAL);
  const set = useCallback(<K extends keyof ExploreFilters>(key: K, value: ExploreFilters[K]) => setFilters((f) => ({ ...f, [key]: value })), []);

  const toggleVenue = useCallback((venue: string) => setFilters((f) => ({ ...f, venues: toggled(f.venues, venue) })), []);
  const setWhen = useCallback((when: When) => setFilters((f) => ({ ...f, when, day: null })), []);
  /** Tapping the picked day again goes back to any date. */
  const pickDay = useCallback(
    (iso: string) => setFilters((f) => (f.day === iso ? { ...f, when: "all", day: null } : { ...f, when: "day", day: iso })),
    [],
  );
  const clear = useCallback(() => setFilters((f) => ({ ...INITIAL, group: f.group })), []);
  const activeCount = activeFilterCount(filters);

  return { filters, set, toggleVenue, setWhen, pickDay, clear, active: activeCount > 0, activeCount };
}
