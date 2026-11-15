import { useCallback, useMemo } from "react";
import { FlatList, Platform, Text, View, useWindowDimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { fluid } from "../../../design/fluid";
import { spacing, typography } from "../../../design/tokens";
import { cardRows, exploreRows } from "../application/explore";
import { homeLayout } from "../application/home-layout";
import { BrandLogo } from "./BrandLogo";
import { ExploreProvider } from "./explore/explore-context";
import { BLOCK_GAP, BLOCK_MIN_WIDTH, CARD_GAP, CARD_MIN_WIDTH } from "./explore/explore.constants";
import { ExploreFooter } from "./explore/ExploreFooter";
import type { ListRow } from "./explore/ExploreRowView";
import { ExploreRowView } from "./explore/ExploreRowView";
import { useExplore } from "./explore/use-explore";
import { HomeSection } from "./HomeSection";
import { END_REACHED_THRESHOLD, PHONE_WIDTH } from "./HomeScreen.constants";
import { headlineSizing, styles } from "./HomeScreen.styles";
import { homeStrings } from "./strings";

/**
 * The home is one virtualised list: the sections are its header, then the explore filters and the
 * explore listing (group titles, day blocks or cards) are its rows, so only the visible rows are drawn.
 */
export function HomeScreen() {
  const { width } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const layout = homeLayout(width);
  const gutter = width < PHONE_WIDTH ? spacing.md : spacing.xl;
  // iOS insets the content under the status bar by itself; Android draws edge to edge.
  const paddingTop = Platform.OS === "android" ? insets.top + spacing.md : spacing.md;

  const explore = useExplore();
  // Wide screens get cards side by side; phones get compact day blocks.
  const cards = layout.kind === "split";
  const listWidth = width - 2 * gutter;
  const [minWidth, gap] = cards ? [CARD_MIN_WIDTH, CARD_GAP] : [BLOCK_MIN_WIDTH, BLOCK_GAP];
  const columns = Math.max(1, Math.floor((listWidth + gap) / (minWidth + gap)));
  const itemWidth = (listWidth - (columns - 1) * gap) / columns;
  const rows = useMemo<ListRow[]>(
    () => [FILTERS_ROW, ...(cards ? cardRows(explore.groups, columns) : exploreRows(explore.groups, columns))],
    [cards, explore.groups, columns],
  );

  const renderItem = useCallback(
    ({ item }: { item: ListRow }) => <ExploreRowView row={item} apiBase={explore.apiBase} itemWidth={itemWidth} />,
    [explore.apiBase, itemWidth],
  );

  const header = (
    <View style={styles.header}>
      <BrandLogo size={fluid(typography.logo.size, width)} />
      <Text accessibilityRole="header" style={[styles.headline, headlineSizing(fluid(typography.display.size, width))]}>
        {homeStrings.headlineLead}
        <Text style={styles.city}>{homeStrings.headlineCity}</Text>
      </Text>
      {layout.kind === "stacked" ? (
        layout.order.map((section) => <HomeSection key={section} section={section} />)
      ) : (
        <>
          <View style={styles.hero}>
            <View style={{ flex: layout.leftShare }}>
              <HomeSection section={layout.left} />
            </View>
            <View style={{ flex: 1 - layout.leftShare }}>
              <HomeSection section={layout.right} />
            </View>
          </View>
          {layout.below.map((section) => (
            <HomeSection key={section} section={section} />
          ))}
        </>
      )}
    </View>
  );

  return (
    <ExploreProvider value={explore}>
      <FlatList
        style={styles.screen}
        contentInsetAdjustmentBehavior="automatic"
        contentContainerStyle={[styles.content, { paddingHorizontal: gutter, paddingTop }]}
        data={rows}
        keyExtractor={keyOf}
        renderItem={renderItem}
        ItemSeparatorComponent={cards ? CardRowGap : RowGap}
        ListHeaderComponent={header}
        // Wide screens pin the filters while the listing scrolls (index 1: the header counts as 0).
        stickyHeaderIndices={cards ? STICKY_FILTERS : undefined}
        ListFooterComponent={<ExploreFooter />}
        onEndReached={explore.fetchMore}
        onEndReachedThreshold={END_REACHED_THRESHOLD}
        keyboardShouldPersistTaps="handled"
      />
    </ExploreProvider>
  );
}

const keyOf = (row: ListRow) => row.key;
const STICKY_FILTERS = [1];
const FILTERS_ROW: ListRow = { kind: "filters", key: "filters" };
const RowGap = () => <View style={styles.rowGap} />;
const CardRowGap = () => <View style={styles.cardRowGap} />;
