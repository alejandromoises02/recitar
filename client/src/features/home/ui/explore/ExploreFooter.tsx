import { Text, View } from "react-native";
import { SectionError } from "../section/SectionError";
import { useStrings } from "../strings";
import { useExploreContext } from "./explore-context";
import { ERROR_MIN_HEIGHT } from "./explore.constants";
import { ExploreEmpty } from "./ExploreEmpty";
import { styles } from "./ExploreFooter.styles";

/** What sits under the listing rows: loading, error, no results, or the next page on its way. */
export function ExploreFooter() {
  const strings = useStrings();
  const explore = useExploreContext();
  if (explore.isPending)
    return (
      <View style={styles.skeletons}>
        <View style={styles.skeleton} />
        <View style={styles.skeleton} />
      </View>
    );
  if (explore.isError) return <SectionError onRetry={explore.retry} minHeight={ERROR_MIN_HEIGHT} />;
  if (explore.visible === 0 && !explore.hasNextPage) return <ExploreEmpty onClear={explore.clear} />;
  if (explore.isFetchingNextPage || explore.visible === 0) return <Text style={styles.loadingMore}>{strings.loading}</Text>;
  return null;
}
