import { Pressable, Text, View } from "react-native";
import { useStrings } from "../strings";
import { styles } from "./CompactFilterBar.styles";
import { useExploreContext } from "./explore-context";
import { SearchField } from "./SearchField";

/** Phones: once the filter panel scrolls away, this bar stays on top with the search and a way back to every filter. */
export function CompactFilterBar({ onOpenFilters }: { onOpenFilters: () => void }) {
  const explore = useExploreContext();
  const { explore: strings } = useStrings();
  return (
    <View style={styles.bar}>
      <View style={styles.search}>
        <SearchField value={explore.filters.text} onChange={(value) => explore.set("text", value)} />
      </View>
      <Pressable
        onPress={onOpenFilters}
        accessibilityRole="button"
        accessibilityLabel={strings.filtersButtonLabel(explore.activeCount)}
        style={({ pressed }) => [styles.button, explore.activeCount > 0 && styles.buttonActive, pressed && styles.pressed]}
      >
        <Text style={[styles.buttonText, explore.activeCount > 0 && styles.buttonTextActive]}>
          {strings.filtersButton(explore.activeCount)}
        </Text>
      </Pressable>
    </View>
  );
}
