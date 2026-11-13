import { useCallback, useRef, useState } from "react";
import type { LayoutChangeEvent, NativeScrollEvent, NativeSyntheticEvent } from "react-native";
import { FlatList, Pressable, StyleSheet, Text, View, useWindowDimensions } from "react-native";
import { breakpoints, colors, fontFamily, radius, spacing, typography } from "../../../design/tokens";
import type { Show } from "../../events/domain/show";
import { configuredApiBase } from "../../events/infrastructure/events-api";
import { useShows } from "../../events/infrastructure/events-queries";
import { ShowCard, THUMB } from "./ShowCard";
import { homeStrings } from "./strings";

const COUNT = 8;
const GAP = spacing.sm;
const PHONE_CARD = 250;

/** "Próximos": the 8 soonest shows in a horizontal strip. Swipe on phones; arrows on wide screens. */
export function NextUpStrip() {
  const { width: screen } = useWindowDimensions();
  const wide = screen > breakpoints.stacked;
  const [filters] = useState({ limit: COUNT });
  const [now] = useState(() => new Date());
  const [apiBase] = useState(configuredApiBase);
  const { data, isPending, isError, refetch } = useShows(filters);

  const [viewport, setViewport] = useState(0);
  const list = useRef<FlatList<Show>>(null);
  const offset = useRef(0);
  // Wide: four and a bit cards per view, so the cut card says "there is more". Phones: fixed width.
  const cardWidth = wide && viewport > 0 ? (viewport - 4 * GAP) / 4.4 : PHONE_CARD;

  const onLayout = useCallback((e: LayoutChangeEvent) => setViewport(e.nativeEvent.layout.width), []);
  const onScroll = useCallback((e: NativeSyntheticEvent<NativeScrollEvent>) => {
    offset.current = e.nativeEvent.contentOffset.x;
  }, []);
  const page = (direction: 1 | -1) =>
    list.current?.scrollToOffset({ offset: Math.max(0, offset.current + direction * viewport * 0.9), animated: true });
  const renderItem = useCallback(
    ({ item }: { item: Show }) => <ShowCard show={item} now={now} apiBase={apiBase} width={cardWidth} />,
    [now, apiBase, cardWidth],
  );

  const shows = data?.pages[0].items ?? [];
  if (!isPending && !isError && shows.length === 0) return null; // nothing coming up: no section

  return (
    <View style={styles.section} onLayout={onLayout}>
      <View style={styles.header}>
        <Text style={styles.title} accessibilityRole="header">
          {homeStrings.sections.next}
        </Text>
        {wide && shows.length > 0 ? (
          <View style={styles.arrows}>
            <Arrow label={homeStrings.scrollBack} glyph="←" onPress={() => page(-1)} />
            <Arrow label={homeStrings.scrollMore} glyph="→" onPress={() => page(1)} />
          </View>
        ) : null}
      </View>

      {isPending ? (
        <View style={styles.row}>
          {Array.from({ length: wide ? 4 : 2 }, (_, i) => (
            <View key={i} style={[styles.skeleton, { width: cardWidth }]} />
          ))}
        </View>
      ) : isError ? (
        <View style={styles.error}>
          <Text style={styles.errorText}>{homeStrings.loadFailed}</Text>
          <Pressable accessibilityRole="button" onPress={() => refetch()} style={styles.retry} hitSlop={8}>
            <Text style={styles.retryText}>{homeStrings.retry}</Text>
          </Pressable>
        </View>
      ) : (
        <FlatList
          ref={list}
          horizontal
          data={shows}
          keyExtractor={keyOf}
          renderItem={renderItem}
          ItemSeparatorComponent={Separator}
          showsHorizontalScrollIndicator={false}
          snapToInterval={cardWidth + GAP}
          decelerationRate="fast"
          onScroll={onScroll}
          scrollEventThrottle={32}
        />
      )}
    </View>
  );
}

const keyOf = (show: Show) => show.id;
const Separator = () => <View style={{ width: GAP }} />;

function Arrow({ label, glyph, onPress }: { label: string; glyph: string; onPress: () => void }) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      onPress={onPress}
      style={({ pressed }) => [styles.arrow, pressed && styles.arrowPressed]}
    >
      <Text style={styles.arrowGlyph}>{glyph}</Text>
    </Pressable>
  );
}

const CARD_HEIGHT = THUMB + 2 * spacing.xs + 2;

const styles = StyleSheet.create({
  section: { gap: spacing.sm },
  header: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", minHeight: 44 },
  title: {
    fontFamily: typography.label.fontFamily,
    fontSize: typography.label.size.min,
    letterSpacing: typography.label.letterSpacing * typography.label.size.min,
    textTransform: "uppercase",
    color: colors.textMuted,
  },
  arrows: { flexDirection: "row", gap: spacing.xs },
  arrow: {
    width: 44,
    height: 44,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
  },
  arrowPressed: { backgroundColor: colors.primary },
  arrowGlyph: { fontFamily: fontFamily.body, fontSize: 15, color: colors.text },
  row: { flexDirection: "row", gap: GAP, overflow: "hidden" },
  skeleton: { height: CARD_HEIGHT, borderRadius: radius.cardSmall, backgroundColor: colors.surface },
  error: { flexDirection: "row", alignItems: "center", gap: spacing.md, minHeight: CARD_HEIGHT },
  errorText: { fontFamily: fontFamily.body, fontSize: typography.bodySmall.size.min, color: colors.textMuted, flexShrink: 1 },
  retry: { paddingHorizontal: spacing.md, paddingVertical: spacing.xs, borderRadius: radius.pill, backgroundColor: colors.primary },
  retryText: { fontFamily: fontFamily.bodyStrong, fontSize: typography.bodySmall.size.min, color: colors.onPrimary },
});
