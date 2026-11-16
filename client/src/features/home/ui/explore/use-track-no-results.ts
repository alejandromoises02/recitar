import { useEffect, useRef } from "react";
import { tracker } from "../../../analytics/tracker";
import { noResults, type FilterState } from "../../application/filter-event";

/** Tells the analytics what was asked for when the listing comes back empty, once for each combination of filters. */
export function useTrackNoResults(empty: boolean, filters: FilterState) {
  const reported = useRef<string | null>(null);
  useEffect(() => {
    const use = empty ? noResults(filters) : null;
    if (!use) {
      reported.current = null;
      return;
    }
    const key = JSON.stringify(use);
    if (key === reported.current) return;
    reported.current = key;
    tracker().noResults(use);
  }, [empty, filters]);
}
