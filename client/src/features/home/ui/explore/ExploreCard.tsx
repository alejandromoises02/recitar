import { memo } from "react";
import { Text, View } from "react-native";
import type { Show } from "../../../events/domain/show";
import { cardDate, timeLabel } from "../../application/explore";
import { imageSource, initials, moreDatesLabel } from "../../application/show-labels";
import { FittedImage } from "../media/FittedImage";
import { styles } from "./ExploreCard.styles";

type Props = { show: Show; date: Date; apiBase: string; width: number };

/** Wide screens: a show as a card with its photo, date block and "+N fechas". */
export const ExploreCard = memo(function ExploreCard({ show, date, apiBase, width }: Props) {
  const photo = imageSource(show.imageUrl, apiBase);
  const when = cardDate(date);
  const more = moreDatesLabel(show.dates.length);
  const place = `${show.venue} · ${timeLabel(date)}`;
  return (
    <View style={[styles.card, { width }]} accessible accessibilityLabel={`${show.name}. ${when.weekday} ${when.day} ${when.month}. ${place}`}>
      <View style={styles.media}>
        {photo ? (
          <FittedImage uri={photo} style={styles.image} />
        ) : (
          <View style={[styles.image, styles.fallback]}>
            <Text style={styles.initials}>{initials(show.name)}</Text>
          </View>
        )}
        <View style={styles.date}>
          <Text style={styles.dateSmall}>{when.weekday}</Text>
          <Text style={styles.dateDay}>{when.day}</Text>
          <Text style={styles.dateSmall}>{when.month}</Text>
        </View>
        {more ? <Text style={styles.more}>{more}</Text> : null}
      </View>
      <View style={styles.body}>
        <Text style={styles.name} numberOfLines={2}>
          {show.name}
        </Text>
        <Text style={styles.place} numberOfLines={1}>
          {place}
        </Text>
      </View>
    </View>
  );
});
