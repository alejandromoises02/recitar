import { View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { TicketLink } from "../../home/ui/controls/TicketLink";
import { styles } from "./PinnedTicketBar.styles";
import type { OfferLink } from "./ticket-offer";

/** Phones: the page's first ticket button, always at the bottom of the screen. */
export function PinnedTicketBar({ link }: { link: OfferLink }) {
  const insets = useSafeAreaInsets();
  return (
    <View style={[styles.bar, { paddingBottom: insets.bottom + styles.bar.paddingTop }]}>
      <TicketLink url={link.url} label={link.label} detail={link.detail} webHint={link.hint} style={styles.link} />
    </View>
  );
}
