import { memo } from "react";
import { Text, View } from "react-native";
import type { Show } from "../../../events/domain/show";
import { timeLabel } from "../../application/explore";
import { imageSource, initials, moreDatesLabel } from "../../application/show-labels";
import { FittedImage } from "../media/FittedImage";
import { styles } from "./AgendaRow.styles";
import { useLang } from "../../../../i18n/lang-context";

type Props = { show: Show; date: Date; apiBase: string };

export const AgendaRow = memo(function AgendaRow({ show, date, apiBase }: Props) {
  const lang = useLang();
  const photo = imageSource(show.imageUrl, apiBase);
  const more = moreDatesLabel(show.dates.length, lang);
  const place = `${show.venue} · ${timeLabel(date)}`;
  return (
    <View style={styles.row} accessible accessibilityLabel={[show.name, place, more].filter(Boolean).join(". ")}>
      {photo ? (
        <FittedImage uri={photo} style={styles.thumb} />
      ) : (
        <View style={[styles.thumb, styles.fallback]}>
          <Text style={styles.initials}>{initials(show.name)}</Text>
        </View>
      )}
      <View style={styles.text}>
        <Text style={styles.name} numberOfLines={2}>
          {show.name}
        </Text>
        <Text style={styles.place} numberOfLines={1}>
          {place}
          {more ? <Text style={styles.more}>{` · ${more}`}</Text> : null}
        </Text>
      </View>
    </View>
  );
});
