import { memo } from "react";
import { Text, View } from "react-native";
import type { Show } from "../../../events/domain/show";
import { cardDate, timeLabel } from "../../application/explore";
import { imageSource, initials, moreDatesLabel } from "../../application/show-labels";
import { FittedImage } from "../media/FittedImage";
import { styles } from "./ExploreCard.styles";
import { useLang } from "../../../../i18n/lang-context";
import { ShowLink } from "../controls/ShowLink";

type Props = { show: Show; date: Date; timeKnown: boolean; apiBase: string; width: number };

/**
 * Wide screens: a show as a card with its photo, date block and "+N fechas". The link is named by its own
 * visible text (WCAG 2.5.3), so its spoken name always matches what is on screen.
 */
export const ExploreCard = memo(function ExploreCard({ show, date, timeKnown, apiBase, width }: Props) {
  const lang = useLang();
  const photo = imageSource(show.imageUrl, apiBase);
  const when = cardDate(date, lang);
  const more = moreDatesLabel(show.dates.length, lang);
  const place = `${show.venue} · ${timeLabel(date, timeKnown, lang)}`;
  return (
    <View role="listitem" style={{ width }}>
      <ShowLink showId={show.id} style={styles.card}>
        <View style={styles.media}>
          {photo ? (
            <FittedImage uri={photo} style={styles.image} />
          ) : (
            <View style={[styles.image, styles.fallback]} aria-hidden>
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
      </ShowLink>
    </View>
  );
});
