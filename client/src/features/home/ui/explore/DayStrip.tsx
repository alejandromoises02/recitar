import { Pressable, ScrollView, Text, View } from "react-native";
import type { StripDay } from "../../application/explore";
import { pickedDayTile } from "../../application/explore";
import { useStrings } from "../strings";
import { styles } from "./DayStrip.styles";
import { useLang } from "../../../../i18n/lang-context";
import { spokenDate } from "../../application/show-labels";
import { useHydrated } from "../../../../design/hydration";

type Props = {
  now: Date;
  days: StripDay[];
  withShows: Set<string>;
  selected: string | null;
  onSelect: (iso: string) => void;
  onMore: () => void;
};

/**
 * This week's days, then a tile that opens the calendar (or shows the day picked there). The web build
 * pre-renders the strip on the day it is built, not the day it is visited: while the browser hydrates
 * that page the tiles are blank, so its first render matches, and the visitor's week fills them right after.
 */
export function DayStrip({ now, days, withShows, selected, onSelect, onMore }: Props) {
  const lang = useLang();
  const strings = useStrings();
  const hydrated = useHydrated();
  const pickedElsewhere = selected !== null && !days.some((day) => day.iso === selected) ? pickedDayTile(selected, now, lang) : null;
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.scroll} contentContainerStyle={styles.row} role="radiogroup" aria-label={strings.explore.nextDays}>
      {days.map((day, i) => {
        if (!hydrated) {
          return (
            <View key={i} style={styles.day} aria-hidden>
              <Text style={styles.label}> </Text>
              <Text style={styles.number}> </Text>
              <View style={styles.dot} />
            </View>
          );
        }
        const active = day.iso === selected;
        const has = withShows.has(day.iso);
        return (
          <Pressable
            key={day.iso}
            role="radio"
            aria-checked={active}
            aria-label={`${spokenDate(day.iso, now, lang)}${has ? `, ${strings.explore.hasShows}` : ""}`}
            onPress={() => onSelect(day.iso)}
            style={[styles.day, active && styles.dayActive]}
          >
            <Text style={[styles.label, active && styles.textActive]}>{day.label}</Text>
            <Text style={[styles.number, active && styles.textActive]}>{day.day}</Text>
            <View style={[styles.dot, has && styles.dotOn, active && styles.dotActive]} />
          </Pressable>
        );
      })}
      <Pressable
        accessibilityRole="button"
        aria-label={pickedElsewhere ? `${spokenDate(pickedElsewhere.iso, now, lang)}. ${strings.explore.otherDate}` : strings.explore.otherDate}
        onPress={onMore}
        style={[styles.day, styles.more, pickedElsewhere && styles.dayActive]}
      >
        {pickedElsewhere ? (
          <>
            <Text style={[styles.label, styles.textActive]}>{pickedElsewhere.label}</Text>
            <Text style={[styles.number, styles.textActive]}>{pickedElsewhere.day}</Text>
            <Text style={[styles.label, styles.textActive]}>{pickedElsewhere.month}</Text>
          </>
        ) : (
          <Text style={styles.plus}>+</Text>
        )}
      </Pressable>
    </ScrollView>
  );
}
