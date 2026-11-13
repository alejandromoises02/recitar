import { memo } from "react";
import { Text, View } from "react-native";
import type { ExploreRow } from "../../application/explore";
import { homeStrings } from "../strings";
import { DayBlockView } from "./DayBlockView";
import { ExploreCard } from "./ExploreCard";
import { styles } from "./ExploreRowView.styles";

type Props = { row: ExploreRow; apiBase: string; itemWidth: number };

export const ExploreRowView = memo(function ExploreRowView({ row, apiBase, itemWidth }: Props) {
  if (row.kind === "group")
    return (
      <Text style={styles.title} accessibilityRole="header">
        {row.title}
        {row.note ? <Text style={styles.note}>{` · ${row.note}`}</Text> : null}
        <Text style={styles.count}>{`  ${homeStrings.shows(row.count, false)}`}</Text>
      </Text>
    );
  if (row.kind === "cards")
    return (
      <View style={styles.cards}>
        {row.items.map(({ key, show, date }) => (
          <ExploreCard key={key} show={show} date={date} apiBase={apiBase} width={itemWidth} />
        ))}
      </View>
    );
  return (
    <View style={styles.blocks}>
      {row.blocks.map((block) => (
        <DayBlockView key={block.iso} block={block} apiBase={apiBase} width={itemWidth} />
      ))}
    </View>
  );
});
