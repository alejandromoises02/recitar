import { memo } from "react";
import { Text, View } from "react-native";
import type { DayBlock } from "../../application/explore";
import { AgendaRow } from "./AgendaRow";
import { styles } from "./DayBlockView.styles";
import { useLang } from "../../../../i18n/lang-context";
import { spokenDate } from "../../application/show-labels";
import { maxFontScale } from "../../../../design/tokens";

type Props = { block: DayBlock; apiBase: string; width: number };

/** One day: its date once on the left, its shows as compact rows on the right. */
export const DayBlockView = memo(function DayBlockView({ block, apiBase, width }: Props) {
  const lang = useLang();
  return (
    <View style={[styles.block, { width }]}>
      <View
        style={styles.date}
        accessible
        role="heading"
        aria-level={4}
        aria-label={`${spokenDate(block.iso, new Date(), lang)}${block.note ? `, ${block.note}` : ""}`}
      >
        <Text style={styles.small} maxFontSizeMultiplier={maxFontScale.dateColumn}>
          {block.weekday}
        </Text>
        <Text style={styles.day} maxFontSizeMultiplier={maxFontScale.dateColumn}>
          {block.day}
        </Text>
        <Text style={styles.small} maxFontSizeMultiplier={maxFontScale.dateColumn}>
          {block.month}
        </Text>
        {block.note ? (
          <Text style={styles.note} maxFontSizeMultiplier={maxFontScale.dateColumn}>
            {block.note}
          </Text>
        ) : null}
      </View>
      <View style={styles.rows} role="list">
        {block.items.map(({ key, show, date }) => (
          <AgendaRow key={key} show={show} date={date} apiBase={apiBase} />
        ))}
      </View>
    </View>
  );
});
