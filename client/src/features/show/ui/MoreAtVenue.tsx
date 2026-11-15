import { useState } from "react";
import { ScrollView, Text, View } from "react-native";
import type { Show } from "../../events/domain/show";
import { useVenueShows } from "../../events/infrastructure/events-queries";
import { heading } from "../../home/ui/a11y";
import { Pulse } from "../../home/ui/skeleton/Pulse";
import { ExploreCard } from "../../home/ui/explore/ExploreCard";
import { CARD_GAP, CARD_MIN_WIDTH } from "../../home/ui/explore/explore.constants";
import { MORE_AT_VENUE, moreAtVenue } from "../application/show-page";
import { MORE_CARD_MAX_WIDTH } from "./MoreAtVenue.constants";
import { styles } from "./MoreAtVenue.styles";
import { useShowStrings } from "./strings";

type Props = { show: Show; apiBase: string; fillWidth: boolean };

/**
 * Other shows at the same venue as explore cards. Beside the poster (`fillWidth`) as many as fit whole (up to
 * four) share the info column, up to MORE_CARD_MAX_WIDTH each; on phones they keep the home's smallest width
 * in a sideways swipe.
 */
export function MoreAtVenue({ show, apiBase, fillWidth }: Props) {
  const strings = useShowStrings();
  const { data, isPending } = useVenueShows(show.venue);
  const [width, setWidth] = useState(0);
  const others = moreAtVenue(data ?? [], show.id);
  // While loading, placeholders hold the room the cards will take, so the page does not grow under the reader.
  if (!isPending && others.length === 0) return null;

  // Beside the poster only whole cards show: a mouse has no swipe and a hidden scroll would hide the last one.
  const fitting = Math.min(MORE_AT_VENUE, Math.max(1, Math.floor((width + CARD_GAP) / (CARD_MIN_WIDTH + CARD_GAP))));
  const count = fillWidth ? fitting : MORE_AT_VENUE;
  const cardWidth = fillWidth ? Math.min(MORE_CARD_MAX_WIDTH, (width - CARD_GAP * (fitting - 1)) / fitting) : CARD_MIN_WIDTH;
  const shown = others.slice(0, count);

  return (
    <View style={styles.section} onLayout={({ nativeEvent: { layout } }) => setWidth(layout.width)}>
      <Text style={styles.title} {...heading(2)}>
        {strings.moreAt(show.venue)}
      </Text>
      {fillWidth && width === 0 ? null : (
        <ScrollView
          horizontal
          scrollEnabled={!fillWidth}
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.row}
          role={isPending ? undefined : "list"}
        >
          {isPending
            ? Array.from({ length: count }, (_, i) => (
                <Pulse key={i} style={[styles.skeletonCard, { width: cardWidth }]}>
                  <View style={styles.skeletonMedia} />
                  <View style={styles.skeletonBody}>
                    <View style={styles.skeletonName} />
                    <View style={styles.skeletonPlace} />
                  </View>
                </Pulse>
              ))
            : shown.map((other) => (
                <ExploreCard
                  key={other.id}
                  show={other}
                  date={other.dates[0].startsAt}
                  timeKnown={other.dates[0].timeKnown}
                  apiBase={apiBase}
                  width={cardWidth}
                />
              ))}
        </ScrollView>
      )}
    </View>
  );
}
