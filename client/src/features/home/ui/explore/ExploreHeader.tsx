import { Text, View } from "react-native";
import { SectionAside } from "../section/SectionAside";
import { useStrings } from "../strings";
import { useExploreContext } from "./explore-context";
import { styles } from "./ExploreHeader.styles";

export function ExploreHeader() {
  const strings = useStrings();
  const explore = useExploreContext();
  return (
    <View style={styles.section}>
      <View style={styles.header}>
        <Text style={styles.title} accessibilityRole="header">
          {strings.sections.explore}
        </Text>
        {explore.loaded ? <SectionAside>{strings.shows(explore.count, explore.hasNextPage)}</SectionAside> : null}
      </View>
    </View>
  );
}
