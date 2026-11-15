import { Pressable, Text, View } from "react-native";
import { useLang } from "../../../i18n/lang-context";
import type { ShowDateTickets } from "../../events/domain/show";
import { dateTile } from "../application/show-page";
import { styles } from "./DateTiles.styles";

type Props = { dates: ShowDateTickets[]; picked: number; onPick: (index: number) => void; now: Date; label: string };

/** One tile per date (weekday, day, month, time); single choice, the picked one in yellow. */
export function DateTiles({ dates, picked, onPick, now, label }: Props) {
  const lang = useLang();
  return (
    <View style={styles.row} role="radiogroup" aria-label={label}>
      {dates.map((date, index) => {
        const tile = dateTile(date.startsAt, now, lang, date.timeKnown);
        const active = index === picked;
        return (
          <Pressable
            key={date.id}
            role="radio"
            aria-checked={active}
            // No aria-label: the tile is named by its visible text (WCAG 2.5.3), so voice users can say what they see.
            onPress={() => onPick(index)}
            style={[styles.tile, active && styles.active]}
          >
            <Text style={[styles.small, active && styles.activeText]}>{tile.weekday}</Text>
            <Text style={[styles.day, active && styles.activeText]}>{tile.day}</Text>
            <Text style={[styles.small, active && styles.activeText]}>{tile.month}</Text>
            <Text style={[styles.time, active && styles.activeText]}>{tile.time}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}
