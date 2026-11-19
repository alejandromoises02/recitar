import { View } from "react-native";
import { iframeStyle, styles } from "./VenueMap.styles";

type Props = { url: string; label: string };

/** The venue on Google's embedded map; its own links open Google Maps in another tab. */
export function VenueMap({ url, label }: Props) {
  return (
    <View style={styles.frame}>
      <iframe src={url} title={label} loading="lazy" referrerPolicy="no-referrer-when-downgrade" style={iframeStyle} />
    </View>
  );
}
