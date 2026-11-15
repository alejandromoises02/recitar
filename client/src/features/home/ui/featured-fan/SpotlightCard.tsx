import { Text, View } from "react-native";
import type { SharedValue } from "react-native-reanimated";
import Animated, { FadeIn } from "react-native-reanimated";
import type { Featured, Show } from "../../../events/domain/show";
import { longDate, moreDatesLabel, spokenDate } from "../../application/show-labels";
import { ticketTarget, trackedTicketUrl } from "../../application/ticket-target";
import { useStrings } from "../strings";
import { AutoplayBar } from "./AutoplayBar";
import { CARD_SWAP_MS } from "./featured.constants";
import { styles } from "./SpotlightCard.styles";
import { useLang } from "../../../../i18n/lang-context";
import { heading } from "../a11y";
import { TicketLink } from "../controls/TicketLink";
import { ShowLink } from "../controls/ShowLink";

type Props = {
  show: Show;
  kind: Featured["kind"];
  width: number;
  progress: SharedValue<number>;
  showProgress: boolean;
  apiBase: string;
};

export function SpotlightCard({ show, kind, width, progress, showProgress, apiBase }: Props) {
  const { featured } = useStrings();
  const lang = useLang();
  const more = moreDatesLabel(show.dates.length, lang);
  const tickets = ticketTarget(show);

  return (
    <View style={[styles.card, { width }]}>
      <Animated.View key={show.id} entering={FadeIn.duration(CARD_SWAP_MS)}>
        <View style={styles.top}>
          <Text style={styles.tag}>{featured.tag[kind]}</Text>
          <Text style={styles.date} aria-label={spokenDate(show.dates[0].startsAt, new Date(), lang)}>
            {longDate(show.dates[0].startsAt, lang)}
          </Text>
        </View>
        <ShowLink showId={show.id}>
          <Text style={styles.name} numberOfLines={2} {...heading(3)}>
            {show.name}
          </Text>
        </ShowLink>
        <Text style={styles.meta}>
          {show.venue}
          {more ? (
            <>
              {" · "}
              <Text style={styles.more}>{more}</Text>
            </>
          ) : null}
        </Text>
      </Animated.View>
      <View style={styles.actions}>
        <TicketLink url={trackedTicketUrl(apiBase, tickets.eventId, tickets.vendor, "spotlight")} label={featured.cta} webHint={`${tickets.domain}. ${featured.opensNewTab}`} />
        <Text style={styles.source}>
          {featured.ticketsAt} <Text style={styles.sourceDomain}>{tickets.domain}</Text>
        </Text>
      </View>
      <Text style={styles.trust}>{featured.trust}</Text>
      {showProgress ? <AutoplayBar progress={progress} /> : null}
    </View>
  );
}
