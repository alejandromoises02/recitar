import { Text, View } from "react-native";
import { TicketLink } from "../../home/ui/controls/TicketLink";
import type { TicketTarget } from "../application/show-page";
import { styles } from "./TicketActions.styles";
import { useShowStrings } from "./strings";

/** `onlyDomain`: phones, where the button itself is pinned at the bottom; only "Entradas en <domain>" stays here. */
type Props = { targets: TicketTarget[]; when: string; showDomain?: boolean; onlyDomain?: boolean };

/** The ticket button(s) for the picked date: one per vendor, the date under the label. */
export function TicketActions({ targets, when, showDomain = true, onlyDomain = false }: Props) {
  const strings = useShowStrings();
  const several = targets.length > 1;
  return (
    <View style={styles.stack}>
      {onlyDomain ? null : targets.map((target) => {
        const label = several && target.vendor ? strings.ticketsVendor(target.vendor) : strings.tickets;
        return (
          <TicketLink
            key={target.url}
            url={target.url}
            label={label}
            detail={when}
            webHint={`${target.domain}. ${strings.opensNewTab}`}
          />
        );
      })}
      {showDomain && !several ? (
        <Text style={styles.domain}>
          {`${strings.ticketsAt} `}
          <Text style={styles.domainStrong}>{targets[0].domain}</Text>
        </Text>
      ) : null}
    </View>
  );
}
