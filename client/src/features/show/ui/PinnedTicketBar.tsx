import { View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { TicketLink } from "../../home/ui/controls/TicketLink";
import type { TicketTarget } from "../application/show-page";
import { styles } from "./PinnedTicketBar.styles";
import { useShowStrings } from "./strings";

/** Phones: the ticket button for the picked date, always at the bottom of the screen. */
export function PinnedTicketBar({ target, when }: { target: TicketTarget; when: string }) {
  const strings = useShowStrings();
  const insets = useSafeAreaInsets();
  return (
    <View style={[styles.bar, { paddingBottom: insets.bottom + styles.bar.paddingTop }]}>
      <TicketLink url={target.url} label={strings.tickets} detail={when} webHint={`${target.domain}. ${strings.opensNewTab}`} style={styles.link} />
    </View>
  );
}
