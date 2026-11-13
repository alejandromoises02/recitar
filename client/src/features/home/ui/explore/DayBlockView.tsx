import { memo } from "react";
import { Text, View } from "react-native";
import type { DayBlock } from "../../application/explore";
import { AgendaRow } from "./AgendaRow";
import { styles } from "./DayBlockView.styles";

type Props = { block: DayBlock; apiBase: string; width: number };

/** One day: its date once on the left, its shows as compact rows on the right. */
export const DayBlockView = memo(function DayBlockView({ block, apiBase, width }: Props) {
  return (
    <View style={[styles.block, { width }]}>
      <View style={styles.date} accessible accessibilityLabel={`${block.weekday} ${block.day} ${block.month}${block.note ? `, ${block.note}` : ""}`}>
        <Text style={styles.small}>{block.weekday}</Text>
        <Text style={styles.day}>{block.day}</Text>
        <Text style={styles.small}>{block.month}</Text>
        {block.note ? <Text style={styles.note}>{block.note}</Text> : null}
      </View>
      <View style={styles.rows}>
        {block.items.map(({ key, show, date }) => (
          <AgendaRow key={key} show={show} date={date} apiBase={apiBase} />
        ))}
      </View>
    </View>
  );
});
