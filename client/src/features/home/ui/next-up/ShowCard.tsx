import { Image } from "expo-image";
import { memo } from "react";
import { Text, View } from "react-native";
import type { Show } from "../../../events/domain/show";
import { daysUntilLabel, imageSource, initials, shortDate } from "../../application/show-labels";
import { styles } from "./ShowCard.styles";
import { useLang } from "../../../../i18n/lang-context";

type Props = { show: Show; now: Date; apiBase: string; width: number };

export const ShowCard = memo(function ShowCard({ show, now, apiBase, width }: Props) {
  const lang = useLang();
  const next = show.dates[0];
  const when = daysUntilLabel(next.startsAt, now, lang);
  const place = `${show.venue} · ${shortDate(next.startsAt, lang)}`;
  const source = imageSource(show.imageUrl, apiBase);
  return (
    <View style={[styles.card, { width }]} accessible accessibilityLabel={`${show.name}. ${when}. ${place}`}>
      {source ? (
        <Image source={source} style={styles.thumb} contentFit="cover" transition={150} accessibilityIgnoresInvertColors />
      ) : (
        <View style={[styles.thumb, styles.fallback]}>
          <Text style={styles.initials}>{initials(show.name)}</Text>
        </View>
      )}
      <View style={styles.text}>
        <Text style={styles.when}>{when}</Text>
        <Text style={styles.name} numberOfLines={1}>
          {show.name}
        </Text>
        <Text style={styles.place} numberOfLines={1}>
          {place}
        </Text>
      </View>
    </View>
  );
});
