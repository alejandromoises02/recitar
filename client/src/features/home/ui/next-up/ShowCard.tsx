import { Image } from "expo-image";
import { memo } from "react";
import { StyleSheet, Text, View } from "react-native";
import { colors, fontFamily, radius, spacing, typography } from "../../../design/tokens";
import type { Show } from "../../events/domain/show";
import { daysUntilLabel, imageSource, initials, shortDate } from "../application/show-labels";

type Props = { show: Show; now: Date; apiBase: string; width: number };

/** A show in the Próximos strip: photo (or initials), when, name, venue and date. */
export const ShowCard = memo(function ShowCard({ show, now, apiBase, width }: Props) {
  const next = show.dates[0];
  const when = daysUntilLabel(next.startsAt, now);
  const place = `${show.venue} · ${shortDate(next.startsAt)}`;
  const source = imageSource(show.imageUrl, apiBase);
  return (
    <View style={[styles.card, { width }]} accessible accessibilityLabel={`${show.name}. ${when}. ${place}`}>
      {source ? (
        <Image source={source} style={styles.thumb} contentFit="cover" transition={150} accessibilityIgnoresInvertColors />
      ) : (
        <View style={[styles.thumb, styles.fallback]}>
          <Text style={styles.initials}>{initials(show.name)}</Text>
        </View>
      )}
      <View style={styles.text}>
        <Text style={styles.when}>{when}</Text>
        <Text style={styles.name} numberOfLines={1}>
          {show.name}
        </Text>
        <Text style={styles.place} numberOfLines={1}>
          {place}
        </Text>
      </View>
    </View>
  );
});

export const THUMB = 60;

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    padding: spacing.xs,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.cardSmall,
    backgroundColor: colors.surface,
  },
  thumb: { width: THUMB, height: THUMB, borderRadius: radius.thumb },
  fallback: { alignItems: "center", justifyContent: "center", backgroundColor: colors.imageFallback },
  initials: { fontFamily: fontFamily.display, fontSize: 18, color: colors.text },
  text: { flex: 1, minWidth: 0, gap: 2 },
  when: {
    fontFamily: fontFamily.bodyStrong,
    fontSize: typography.label.size.min,
    letterSpacing: 0.1 * typography.label.size.min,
    textTransform: "uppercase",
    color: colors.accent,
  },
  name: { fontFamily: fontFamily.bodyStrong, fontSize: typography.body.size.min, color: colors.text },
  place: { fontFamily: fontFamily.body, fontSize: typography.bodySmall.size.min, color: colors.textMuted },
});
