import { useState } from "react";
import { Text, View } from "react-native";
import { announcedFrom } from "../../events/application/announced-from";
import { useShows } from "../../events/infrastructure/events-queries";
import type { HomeSection } from "../application/home-layout";
import { ANNOUNCED_COUNT, EXPLORE_PREVIEW_COUNT, NEXT_UP_COUNT } from "./home.constants";
import { styles } from "./SectionSlot.styles";
import { homeStrings } from "./strings";

type SlotSection = Exclude<HomeSection, "featured">;

type Props = { section: SlotSection; minHeight: number };

/** Placeholder for a section not built yet; it already queries that section's data. */
export function SectionSlot({ section, minHeight }: Props) {
  return (
    <View style={[styles.slot, { minHeight }]}>
      <Text style={styles.label}>{homeStrings.sections[section]}</Text>
      <ShowsStatus section={section} />
    </View>
  );
}

function ShowsStatus({ section }: { section: SlotSection }) {
  // Kept in state so the query key stays the same across renders.
  const [filters] = useState(() =>
    section === "justAnnounced"
      ? { sort: "announced" as const, announced_from: announcedFrom(new Date()), limit: ANNOUNCED_COUNT }
      : { limit: section === "next" ? NEXT_UP_COUNT : EXPLORE_PREVIEW_COUNT },
  );
  const { data, isPending, isError, hasNextPage } = useShows(filters);
  if (isPending) return <Text style={styles.status}>{homeStrings.loading}</Text>;
  if (isError) return <Text style={[styles.status, styles.error]}>{homeStrings.loadFailed}</Text>;
  return <Text style={styles.status}>{homeStrings.shows(data.pages[0].items.length, hasNextPage)}</Text>;
}
