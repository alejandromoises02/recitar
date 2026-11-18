import { useExploreContext } from "./explore-context";
import { ExploreFilters } from "./ExploreFilters";

/** The explore filters wired to the shared explore state: the list panel and the phone sheet both use it. */
export function BoundExploreFilters() {
  const explore = useExploreContext();
  return (
    <ExploreFilters
      now={explore.now}
      filters={explore.filters}
      venues={explore.venues}
      days={explore.days}
      daysWithShows={explore.marked}
      active={explore.active}
      onText={(value) => explore.set("text", value)}
      onVenue={explore.toggleVenue}
      onAllVenues={() => explore.set("venues", [])}
      onWhen={explore.setWhen}
      onDay={explore.pickDay}
      onGroup={(value) => explore.set("group", value)}
      onClear={explore.clear}
    />
  );
}
