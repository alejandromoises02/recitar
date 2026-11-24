import * as Linking from "expo-linking";
import { useIsFocused } from "expo-router";
import { View } from "react-native";
import { WebView } from "react-native-webview";
import { EMBED_PREFIX } from "./SpotifyPlayer.constants";
import { styles } from "./SpotifyPlayer.styles";
import { useAppActive } from "./use-app-active";

type Props = { url: string; label: string };

/**
 * The artist's Spotify player, in a WebView. Its links ("open in Spotify", a track) open the Spotify
 * app or the browser. The stack keeps a show page mounted after leaving it, and a mounted player keeps
 * playing: it is removed while the page is not the one in view, or the app is in the background.
 */
export function SpotifyPlayer({ url, label }: Props) {
  const appActive = useAppActive();
  const inView = useIsFocused() && appActive;
  return (
    <View style={styles.frame} accessibilityLabel={label}>
      {inView ? (
        <WebView
          source={{ uri: url }}
          style={styles.player}
          allowsInlineMediaPlayback
          setSupportMultipleWindows
          onOpenWindow={(event) => void Linking.openURL(event.nativeEvent.targetUrl)}
          onShouldStartLoadWithRequest={(request) => {
            if (!request.isTopFrame || request.url.startsWith(EMBED_PREFIX)) return true;
            void Linking.openURL(request.url);
            return false;
          }}
        />
      ) : null}
    </View>
  );
}
