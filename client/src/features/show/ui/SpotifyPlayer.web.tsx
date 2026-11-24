import { useIsFocused } from "expo-router";
import { View } from "react-native";
import { PLAYER_ALLOW } from "./SpotifyPlayer.constants";
import { iframeStyle, styles } from "./SpotifyPlayer.styles";

type Props = { url: string; label: string };

/**
 * The artist's Spotify player: it plays their top tracks without leaving the page.
 * The router keeps a show page mounted after leaving it (for another show, or back to the listing),
 * and an iframe left mounted keeps playing: it is removed while the page is not the one in view.
 */
export function SpotifyPlayer({ url, label }: Props) {
  const inView = useIsFocused();
  return <View style={styles.frame}>{inView ? <iframe src={url} title={label} loading="lazy" allow={PLAYER_ALLOW} style={iframeStyle} /> : null}</View>;
}
