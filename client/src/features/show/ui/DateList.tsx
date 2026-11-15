import { Text, View } from "react-native";
import { useLang } from "../../../i18n/lang-context";
import type { ShowDateTickets } from "../../events/domain/show";
import { buttonWhen } from "../application/show-page";
import { styles } from "./DateList.styles";
import { useShowStrings } from "./strings";

/** Every date, listed: the date is picked on the ticketer's page, so nothing here is selectable. */
export function DateList({ dates, now }: { dates: ShowDateTickets[]; now: Date }) {
  const lang = useLang();
  const strings = useShowStrings();
  return (
    <View style={styles.list} role="list">
      {dates.map((date) => (
        <View key={date.id} style={styles.row} role="listitem">
          <Text style={styles.when}>{buttonWhen(date.startsAt, now, lang)}</Text>
          {date.ticketLinks.length === 0 ? <Text style={styles.soon}>{strings.notOnSale}</Text> : null}
        </View>
      ))}
    </View>
  );
}
