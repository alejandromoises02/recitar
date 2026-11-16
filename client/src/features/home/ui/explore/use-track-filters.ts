import { useEffect, useRef } from "react";
import { tracker } from "../../../analytics/tracker";
import { filterUsed, type FilterState } from "../../application/filter-event";

/** Tells the analytics which filter was just used, comparing each state with the one before it. */
export function useTrackFilters(filters: FilterState) {
  const before = useRef(filters);
  useEffect(() => {
    const use = filterUsed(before.current, filters);
    before.current = filters;
    if (use) tracker().filterUsed(use);
  }, [filters]);
}
