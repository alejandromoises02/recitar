import { memo } from "react";
import { Text, View } from "react-native";
import Animated from "react-native-reanimated";
import type { Show } from "../../../events/domain/show";
import { boardDate, imageSource, moreDatesLabel, spokenDate } from "../../application/show-labels";
import type { BoardGeometry } from "./board.constants";
import { ROW_HEIGHT_EM, SUB_TEXT_EM } from "./board.constants";
import { boardText, styles } from "./BoardRow.styles";
import { Flap } from "./Flap";
import { PhotoStrip } from "./PhotoStrip";
import { useFlipIn } from "./use-flip-in";
import { useLang } from "../../../../i18n/lang-context";
import { maxFontScale } from "../../../../design/tokens";

type Props = { show: Show; index: number; now: Date; apiBase: string; geometry: BoardGeometry };

export const BoardRow = memo(function BoardRow({ show, index, now, apiBase, geometry }: Props) {
  const lang = useLang();
  const { flapSize, dateWidth, photoShare } = geometry;
  const date = boardDate(show.dates[0].startsAt, now, lang);
  const more = moreDatesLabel(show.dates.length, lang);
  const photo = imageSource(show.imageUrl, apiBase);
  const flip = useFlipIn(index);
  const minHeight = flapSize * ROW_HEIGHT_EM;
  const text = boardText(flapSize);

  return (
    <Animated.View
      style={[styles.row, flip]}
      accessible
      role="listitem"
      aria-label={[show.name, show.venue, spokenDate(show.dates[0].startsAt, now, lang), more].filter(Boolean).join(". ")}
    >
      <Flap style={[styles.dateFlap, { width: dateWidth, minHeight }]}>
        <Text style={[text, styles.date]} maxFontSizeMultiplier={maxFontScale.fixedCell}>
          {date}
        </Text>
      </Flap>
      <Flap style={[styles.nameFlap, { minHeight, paddingRight: photo ? `${photoShare * 100}%` : undefined }]}>
        {photo ? <PhotoStrip uri={photo} share={photoShare} /> : null}
        <View style={photo ? styles.nameBesidePhoto : undefined}>
          <Text style={[text, styles.name]} numberOfLines={2}>
            {show.name}
          </Text>
          <Text style={[styles.sub, { fontSize: flapSize * SUB_TEXT_EM }]} numberOfLines={1}>
            {show.venue}
            {more ? (
              <>
                {" · "}
                <Text style={styles.more}>{more}</Text>
              </>
            ) : null}
          </Text>
        </View>
      </Flap>
    </Animated.View>
  );
});
