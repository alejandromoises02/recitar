import { useState } from "react";
import { Linking, Text, View } from "react-native";
import type { Show } from "../../events/domain/show";
import { imageSource, initials } from "../../home/application/show-labels";
import { FittedImage } from "../../home/ui/media/FittedImage";
import { POSTER_RATIO } from "./show.constants";
import { styles } from "./ShowPoster.styles";
import { useShowStrings } from "./strings";


/** The show's photo, whole, in a frame shaped like it; the credit when the photo is licensed. */
export function ShowPoster({ show, apiBase, minRatio = POSTER_RATIO.min }: { show: Show; apiBase: string; minRatio?: number }) {
  const strings = useShowStrings();
  const [ratio, setRatio] = useState<number>(POSTER_RATIO.fallback);
  const photo = imageSource(show.imageUrl, apiBase);
  const licensed = show.imageOrigin === "licensed" && show.imageAuthor;
  return (
    <View style={[styles.frame, { aspectRatio: Math.min(POSTER_RATIO.max, Math.max(minRatio, photo ? ratio : POSTER_RATIO.fallback)) }]}>
      {photo ? (
        <FittedImage uri={photo} style={styles.fill} onLoad={({ source }) => source.height > 0 && setRatio(source.width / source.height)} />
      ) : (
        <View style={[styles.fill, styles.fallback]} aria-hidden>
          <Text style={styles.initials}>{initials(show.name)}</Text>
        </View>
      )}
      {photo && licensed ? (
        <View style={styles.credit}>
          <Text style={styles.creditText}>
            {`${strings.photo}: `}
            <Text style={styles.creditLink} accessibilityRole="link" onPress={() => show.imageSourceUrl && Linking.openURL(show.imageSourceUrl)}>
              {show.imageAuthor}
            </Text>
            {show.imageLicense ? ` · ${show.imageLicense}` : ""}
          </Text>
        </View>
      ) : null}
    </View>
  );
}
