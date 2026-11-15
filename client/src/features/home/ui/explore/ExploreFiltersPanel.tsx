import { View } from "react-native";
import { useExploreContext } from "./explore-context";
import { ExploreFilters } from "./ExploreFilters";
import { styles } from "./ExploreFiltersPanel.styles";

/** The explore filters as a list row, so wide screens can pin it to the top while scrolling. */
export function ExploreFiltersPanel() {
  const explore = useExploreContext();
  return (
    <View style={styles.backing}>
      <ExploreFilters
        now={explore.now}
        filters={explore.filters}
        venues={explore.venueNames}
        days={explore.days}
        daysWithShows={explore.marked}
        active={explore.active}
        onText={(value) => explore.set("text", value)}
        onVenue={(value) => explore.set("venue", value)}
        onWhen={explore.setWhen}
        onDay={explore.pickDay}
        onGroup={(value) => explore.set("group", value)}
        onClear={explore.clear}
      />
    </View>
  );
}
