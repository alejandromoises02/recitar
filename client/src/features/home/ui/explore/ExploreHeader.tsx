import { Text, View } from "react-native";
import { SectionAside } from "../section/SectionAside";
import { homeStrings } from "../strings";
import { useExploreContext } from "./explore-context";
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
    </View>
  );
}
