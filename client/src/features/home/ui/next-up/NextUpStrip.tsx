import { useCallback, useRef, useState } from "react";
import type { LayoutChangeEvent, NativeScrollEvent, NativeSyntheticEvent } from "react-native";
import { FlatList, Platform, View, useWindowDimensions } from "react-native";
import { breakpoints } from "../../../../design/tokens";
import type { Show } from "../../../events/domain/show";
import { configuredApiBase } from "../../../events/infrastructure/events-api";
import { useShows } from "../../../events/infrastructure/events-queries";
import { NEXT_UP_COUNT } from "../home.constants";
import { SectionError } from "../section/SectionError";
import { SectionHeader } from "../section/SectionHeader";
import { useStrings } from "../strings";
import { ArrowButton } from "../controls/ArrowButton";
import { CARDS_PER_VIEW, CARD_GAP, CARD_HEIGHT, PAGE_FRACTION, PHONE_CARD_WIDTH, SKELETON_CARDS } from "./NextUpStrip.constants";
import { Pulse } from "../skeleton/Pulse";
import { styles } from "./NextUpStrip.styles";
import { ShowCard } from "./ShowCard";

export function NextUpStrip() {
  const strings = useStrings();
  const { width: screen } = useWindowDimensions();
  const wide = screen > breakpoints.stacked;
  const [filters] = useState({ limit: NEXT_UP_COUNT });
  const [now] = useState(() => new Date());
  const [apiBase] = useState(configuredApiBase);
  const { data, isPending, isError, refetch } = useShows(filters);

  const [viewport, setViewport] = useState(0);
  const list = useRef<FlatList<Show>>(null);
  const offset = useRef(0);
  const cardWidth = wide && viewport > 0 ? (viewport - 4 * CARD_GAP) / CARDS_PER_VIEW : PHONE_CARD_WIDTH;

  const onLayout = useCallback((e: LayoutChangeEvent) => setViewport(e.nativeEvent.layout.width), []);
  const onScroll = useCallback((e: NativeSyntheticEvent<NativeScrollEvent>) => {
    offset.current = e.nativeEvent.contentOffset.x;
  }, []);
  const page = (direction: 1 | -1) =>
    list.current?.scrollToOffset({ offset: Math.max(0, offset.current + direction * viewport * PAGE_FRACTION), animated: true });
  const renderItem = useCallback(
    ({ item }: { item: Show }) => <ShowCard show={item} now={now} apiBase={apiBase} width={cardWidth} />,
    [now, apiBase, cardWidth],
  );

  const shows = data?.pages[0].items ?? [];
  if (!isPending && !isError && shows.length === 0) return null;

  return (
    <View style={styles.section} onLayout={onLayout}>
      <SectionHeader title={strings.sections.next}>
        {wide && shows.length > 0 ? (
          <View style={styles.arrows}>
            <ArrowButton label={strings.scrollBack} glyph="←" onPress={() => page(-1)} />
            <ArrowButton label={strings.scrollMore} glyph="→" onPress={() => page(1)} />
          </View>
        ) : null}
      </SectionHeader>

      {isPending ? (
        <View style={styles.row}>
          {Array.from({ length: wide ? SKELETON_CARDS.wide : SKELETON_CARDS.phone }, (_, i) => (
            <Pulse key={i} style={[styles.skeleton, { width: cardWidth }]} />
          ))}
        </View>
      ) : isError ? (
        <SectionError onRetry={() => refetch()} minHeight={CARD_HEIGHT} />
      ) : (
        <FlatList
          ref={list}
          horizontal
          data={shows}
          keyExtractor={keyOf}
          renderItem={renderItem}
          ItemSeparatorComponent={Separator}
          showsHorizontalScrollIndicator={false}
          snapToInterval={cardWidth + CARD_GAP}
          decelerationRate="fast"
          onScroll={onScroll}
          scrollEventThrottle={32}
          // The cards are not focusable, so on web the strip itself is: Tab reaches it and the arrow keys scroll it.
          {...(Platform.OS === "web" ? { tabIndex: 0, role: "region", "aria-label": strings.sections.next } : {})}
        />
      )}
    </View>
  );
}

const keyOf = (show: Show) => show.id;
const Separator = () => <View style={styles.separator} />;
