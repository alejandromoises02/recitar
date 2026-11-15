import * as WebBrowser from "expo-web-browser";
import { Pressable, Text, View } from "react-native";
import type { SharedValue } from "react-native-reanimated";
import Animated, { FadeIn } from "react-native-reanimated";
import type { Featured, Show } from "../../../events/domain/show";
import { longDate, moreDatesLabel } from "../../application/show-labels";
import { ticketTarget } from "../../application/ticket-target";
import { useStrings } from "../strings";
import { AutoplayBar } from "./AutoplayBar";
import { CARD_SWAP_MS } from "./featured.constants";
import { styles } from "./SpotlightCard.styles";
import { useLang } from "../../../../i18n/lang-context";

type Props = {
  show: Show;
  kind: Featured["kind"];
  width: number;
  progress: SharedValue<number>;
  showProgress: boolean;
};

export function SpotlightCard({
  show,
  kind,
  width,
  progress,
  showProgress,
}: Props) {
  const { featured } = useStrings();
  const lang = useLang();
  const more = moreDatesLabel(show.dates.length, lang);
  const tickets = ticketTarget(show);

  return (
    <View style={[styles.card, { width }]}>
      <Animated.View key={show.id} entering={FadeIn.duration(CARD_SWAP_MS)}>
        <View style={styles.top}>
          <Text style={styles.tag}>{featured.tag[kind]}</Text>
          <Text style={styles.date}>{longDate(show.dates[0].startsAt, lang)}</Text>
        </View>
        <Text style={styles.name} numberOfLines={2} accessibilityRole="header">
          {show.name}
        </Text>
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
        <Pressable
          accessibilityRole="link"
          onPress={() => WebBrowser.openBrowserAsync(tickets.url)}
          style={({ pressed }) => [styles.cta, pressed && styles.ctaPressed]}
        >
          <View style={styles.ctaIcon}>
            <Text style={styles.ctaIconText} aria-hidden>
              ↗
            </Text>
          </View>
          <Text style={styles.ctaText}>{featured.cta}</Text>
        </Pressable>
        <Text style={styles.source}>
          {featured.ticketsAt}{" "}
          <Text style={styles.sourceDomain}>{tickets.domain}</Text>
        </Text>
      </View>
      <Text style={styles.trust}>{featured.trust}</Text>
      {showProgress ? <AutoplayBar progress={progress} /> : null}
    </View>
  );
}
