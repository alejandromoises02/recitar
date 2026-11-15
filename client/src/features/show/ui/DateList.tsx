import { Text, View } from "react-native";
import { useLang } from "../../../i18n/lang-context";
import type { ShowDateTickets } from "../../events/domain/show";
import { boardDate, daysUntil, daysUntilLabel, startTime } from "../../home/application/show-labels";
import { Flap } from "../../home/ui/announced-board/Flap";
import { styles } from "./DateList.styles";
import { useShowStrings } from "./strings";

/** Every date, listed on board rows: the date is picked on the ticketer's page, so nothing here is selectable. */
export function DateList({ dates, now }: { dates: ShowDateTickets[]; now: Date }) {
  const lang = useLang();
  const strings = useShowStrings();
  return (
    <View style={styles.list} role="list">
      {dates.map((date) => (
        <Flap key={date.id} style={styles.row} role="listitem">
          <Text style={styles.date}>{boardDate(date.startsAt, now, lang)}</Text>
          <Text style={styles.time}>{startTime(date.startsAt, date.timeKnown, lang, "short")}</Text>
          <Text style={[styles.until, daysUntil(date.startsAt, now) <= 1 && styles.soon]} numberOfLines={1}>
            {daysUntilLabel(date.startsAt, now, lang)}
          </Text>
          {date.ticketLinks.length === 0 ? <Text style={styles.notOnSale}>{strings.notOnSale}</Text> : null}
        </Flap>
      ))}
    </View>
  );
}
