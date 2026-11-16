import { Text, View } from "react-native";
import { SectionAside } from "../section/SectionAside";
import { useStrings } from "../strings";
import { useExploreContext } from "./explore-context";
import { styles } from "./ExploreHeader.styles";
import { listingStatus } from "../../application/explore";
import { heading } from "../a11y";
import { StatusAnnouncer } from "./StatusAnnouncer";
import { useTrackNoResults } from "./use-track-no-results";

export function ExploreHeader() {
  const strings = useStrings();
  const explore = useExploreContext();
  const status = listingStatus(explore);
  const message =
    status === null
      ? null
      : status.kind === "error"
        ? strings.loadFailed
        : status.kind === "empty"
          ? strings.explore.empty
          : strings.explore.found(strings.shows(status.count, status.more));
  const { text, venue, when, day } = explore.filters;
  useTrackNoResults(status?.kind === "empty", explore.filters);
  return (
    <View style={styles.section}>
      <View style={styles.header}>
        <Text style={styles.title} {...heading(2)}>
          {strings.sections.explore}
        </Text>
        {explore.loaded ? <SectionAside>{strings.shows(explore.count, explore.hasNextPage)}</SectionAside> : null}
      </View>
      <StatusAnnouncer message={message} filtersKey={[text.trim(), venue, when, day].join("|")} urgent={status?.kind === "error"} />
    </View>
  );
}
