import { memo } from "react";
import { Text, View } from "react-native";
import type { Show } from "../../../events/domain/show";
import { timeLabel } from "../../application/explore";
import { imageSource, initials, moreDatesLabel } from "../../application/show-labels";
import { FittedImage } from "../media/FittedImage";
import { styles } from "./AgendaRow.styles";
import { useLang } from "../../../../i18n/lang-context";
import { ShowLink } from "../controls/ShowLink";

type Props = { show: Show; date: Date; timeKnown: boolean; apiBase: string };

export const AgendaRow = memo(function AgendaRow({ show, date, timeKnown, apiBase }: Props) {
  const lang = useLang();
  const photo = imageSource(show.imageUrl, apiBase);
  const more = moreDatesLabel(show.dates.length, lang);
  const place = `${show.venue} · ${timeLabel(date, timeKnown, lang)}`;
  return (
    <View role="listitem">
      <ShowLink showId={show.id} label={[show.name, place, more].filter(Boolean).join(". ")} style={styles.row}>
        {photo ? (
          <FittedImage uri={photo} style={styles.thumb} />
        ) : (
          <View style={[styles.thumb, styles.fallback]} aria-hidden>
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
      </ShowLink>
    </View>
  );
});
