import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { colors, radius, spacing, typography } from "../../../design/tokens";
import { announcedFrom } from "../../events/application/announced-from";
import { useFeatured, useShows } from "../../events/infrastructure/events-queries";
import type { HomeSection } from "../application/home-layout";
import { homeStrings } from "./strings";

/** Stand-in for a section until its own task builds it (cli02 T2-T6). It already reads the data
 * the section will use, so a phone shows whether the API answers. */
export function SectionSlot({ section, minHeight }: { section: HomeSection; minHeight: number }) {
  return (
    <View style={[styles.slot, { minHeight }]}>
      <Text style={styles.label}>{homeStrings.sections[section]}</Text>
      {section === "featured" ? <FeaturedStatus /> : <ShowsStatus section={section} />}
    </View>
  );
}

function FeaturedStatus() {
  const { data, isPending, isError } = useFeatured();
  if (isPending) return <Text style={styles.status}>{homeStrings.loading}</Text>;
  if (isError) return <Text style={[styles.status, styles.error]}>{homeStrings.loadFailed}</Text>;
  return (
    <Text style={styles.status}>
      {homeStrings.shows(data.items.length, false)} · {homeStrings.featuredKind[data.kind]}
    </Text>
  );
}

function ShowsStatus({ section }: { section: Exclude<HomeSection, "featured"> }) {
  // Fixed on first render, so the query key (and its cache entry) does not change every render.
  const [filters] = useState(() =>
    section === "justAnnounced"
      ? { sort: "announced" as const, announced_from: announcedFrom(new Date()), limit: 12 }
      : { limit: section === "next" ? 8 : 20 },
  );
  const { data, isPending, isError, hasNextPage } = useShows(filters);
  if (isPending) return <Text style={styles.status}>{homeStrings.loading}</Text>;
  if (isError) return <Text style={[styles.status, styles.error]}>{homeStrings.loadFailed}</Text>;
  return <Text style={styles.status}>{homeStrings.shows(data.pages[0].items.length, hasNextPage)}</Text>;
}

const styles = StyleSheet.create({
  slot: {
    borderWidth: 1,
    borderStyle: "dashed",
    borderColor: colors.line,
    borderRadius: radius.card,
    backgroundColor: colors.surface,
    padding: spacing.md,
    gap: spacing.xs,
  },
  label: {
    fontFamily: typography.label.fontFamily,
    fontSize: typography.label.size.min,
    letterSpacing: typography.label.letterSpacing * typography.label.size.min,
    textTransform: "uppercase",
    color: colors.accent,
  },
  status: { fontFamily: typography.body.fontFamily, fontSize: typography.bodySmall.size.min, color: colors.textMuted },
  error: { color: colors.text },
});
