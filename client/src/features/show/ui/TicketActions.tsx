import { Text, View } from "react-native";
import { TicketLink } from "../../home/ui/controls/TicketLink";
import { styles } from "./TicketActions.styles";
import type { TicketOffer } from "./ticket-offer";

/** `onlyNote`: phones, where the button itself is pinned at the bottom; only the line under it stays here. */
type Props = { offer: TicketOffer; onlyNote?: boolean };

/** The ticket button(s) and the line under them: where to buy, or how the date is picked, or not on sale yet. */
export function TicketActions({ offer, onlyNote = false }: Props) {
  return (
    <View style={styles.stack}>
      {onlyNote
        ? null
        : offer.links.map((link) => <TicketLink key={link.url} url={link.url} label={link.label} detail={link.detail} webHint={link.hint} />)}
      {offer.note ? <Text style={styles.domain}>{offer.note}</Text> : null}
    </View>
  );
}
