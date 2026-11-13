import { Text, View } from "react-native";
import { SectionAside } from "../section/SectionAside";
import { homeStrings } from "../strings";
import { useExploreContext } from "./explore-context";
import { ExploreFilters } from "./ExploreFilters";
import { styles } from "./ExploreHeader.styles";

export function ExploreHeader() {
  const explore = useExploreContext();
  return (
    <View style={styles.section}>
      <View style={styles.header}>
        <Text style={styles.title} accessibilityRole="header">
          {homeStrings.sections.explore}
        </Text>
        {explore.loaded ? <SectionAside>{homeStrings.shows(explore.count, explore.hasNextPage)}</SectionAside> : null}
      </View>
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
