import { memo } from "react";
import { View, type LayoutChangeEvent } from "react-native";
import Animated, { FadeIn } from "react-native-reanimated";
import type { ExploreRow } from "../../application/explore";
import { DayBlockView } from "./DayBlockView";
import { ExploreCard } from "./ExploreCard";
import { ExploreFiltersPanel } from "./ExploreFiltersPanel";
import { GroupTitle } from "./GroupTitle";
import { GROUP_FADE_MS } from "./explore.constants";
import { styles } from "./ExploreRowView.styles";

/** A row of the home list: the explore filters, or a listing row. */
export type ListRow = ExploreRow | { kind: "filters"; key: string };

/**
 * `fadeIn`: the row belongs to the group just unfolded. `updating`: it shows the previous filter's results while
 * the new ones load. `onPanelLayout`: measures the filter panel row.
 */
type Props = {
  row: ListRow;
  apiBase: string;
  itemWidth: number;
  fadeIn: boolean;
  updating?: boolean;
  onPanelLayout?: (event: LayoutChangeEvent) => void;
};

const ENTERING = FadeIn.duration(GROUP_FADE_MS);

export const ExploreRowView = memo(function ExploreRowView({ row, apiBase, itemWidth, fadeIn, updating = false, onPanelLayout }: Props) {
  const entering = fadeIn ? ENTERING : undefined;
  if (row.kind === "filters") return <ExploreFiltersPanel onLayout={onPanelLayout} />;
  if (row.kind === "group")
    return (
      <View style={updating && styles.updating}>
        <GroupTitle group={row.group} title={row.title} note={row.note} count={row.count} expanded={row.expanded} />
      </View>
    );
  if (row.kind === "cards")
    return (
      <Animated.View entering={entering} style={[styles.cards, updating && styles.updating]} role="list">
        {row.items.map(({ key, show, date, timeKnown }) => (
          <ExploreCard key={key} show={show} date={date} timeKnown={timeKnown} apiBase={apiBase} width={itemWidth} />
        ))}
      </Animated.View>
    );
  return (
    <Animated.View entering={entering} style={[styles.blocks, updating && styles.updating]}>
      {row.blocks.map((block) => (
        <DayBlockView key={block.iso} block={block} apiBase={apiBase} width={itemWidth} />
      ))}
    </Animated.View>
  );
});
