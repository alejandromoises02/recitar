import * as Linking from "expo-linking";
import { useIsFocused } from "expo-router";
import { useEffect, useImperativeHandle, useRef } from "react";
import { View } from "react-native";
import { WebView } from "react-native-webview";
import { spotifyArtistUri, spotifySamplePage } from "../../../show/application/show-page";
import { PLAYER_HEIGHT } from "../../../show/ui/SpotifyPlayer.constants";
import { useAppActive } from "../../../show/ui/use-app-active";
import { styles } from "./SpotifySample.styles";
import type { SampleProps } from "./SpotifySample.types";

const ownPage = (url: string) => url.startsWith("about:") || url.startsWith("data:");

/**
 * The artist's Spotify player through the iFrame API, in a WebView, so the record can play and pause
 * it. Its links open Spotify or the browser. It is removed while the listing is not in view, or the
 * app is in the background (iOS would keep it playing).
 */
export function SpotifySample({ artistId, label, onPlaying, ref }: SampleProps) {
  const appActive = useAppActive();
  const inView = useIsFocused() && appActive;
  const view = useRef<WebView<object>>(null);
  const report = useRef(onPlaying);
  useEffect(() => {
    report.current = onPlaying;
  }, [onPlaying]);

  useImperativeHandle(ref, () => ({ toggle: () => view.current?.injectJavaScript("window.player && window.player.togglePlay(); true;") }), []);
  useEffect(() => (inView ? undefined : report.current(false)), [inView]);
  useEffect(() => () => report.current(false), []);

  return (
    <View style={styles.frame} accessibilityLabel={label}>
      {inView ? (
        <WebView
          ref={view}
          source={{ html: spotifySamplePage(spotifyArtistUri(artistId), PLAYER_HEIGHT) }}
          style={styles.player}
          originWhitelist={["*"]}
          allowsInlineMediaPlayback
          mediaPlaybackRequiresUserAction={false}
          setSupportMultipleWindows
          onOpenWindow={(event) => void Linking.openURL(event.nativeEvent.targetUrl)}
          onMessage={(event) => {
            try {
              report.current(Boolean((JSON.parse(event.nativeEvent.data) as { playing?: unknown }).playing));
            } catch {
              // Not our message: the embed posts its own.
            }
          }}
          onShouldStartLoadWithRequest={(request) => {
            if (!request.isTopFrame || ownPage(request.url)) return true;
            void Linking.openURL(request.url);
            return false;
          }}
        />
      ) : null}
    </View>
  );
}
