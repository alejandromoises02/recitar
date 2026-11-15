import type { LayoutChangeEvent } from "react-native";
import { View } from "react-native";
import { BoundExploreFilters } from "./BoundExploreFilters";
import { styles } from "./ExploreFiltersPanel.styles";

/** The explore filters as a list row, so wide screens can pin it to the top while scrolling. */
export function ExploreFiltersPanel({ onLayout }: { onLayout?: (event: LayoutChangeEvent) => void }) {
  return (
    <View style={styles.backing} onLayout={onLayout}>
      <BoundExploreFilters />
    </View>
  );
}
