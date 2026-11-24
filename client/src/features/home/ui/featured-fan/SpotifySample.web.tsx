import { useIsFocused } from "expo-router";
import { useEffect, useImperativeHandle, useRef } from "react";
import { View } from "react-native";
import { SPOTIFY_IFRAME_API, spotifyArtistUri } from "../../../show/application/show-page";
import { PLAYER_HEIGHT } from "../../../show/ui/SpotifyPlayer.constants";
import { styles } from "./SpotifySample.styles";
import type { SampleProps } from "./SpotifySample.types";

type PlaybackEvent = { data: { isPaused: boolean } };
type Controller = { togglePlay: () => void; destroy: () => void; addListener: (name: "playback_update", handler: (event: PlaybackEvent) => void) => void };
type IFrameApi = {
  createController: (element: HTMLElement, options: { uri: string; width: string; height: number }, ready: (controller: Controller) => void) => void;
};

let api: Promise<IFrameApi> | null = null;

/** Spotify's iFrame API script, loaded once for the whole page. */
function iframeApi(): Promise<IFrameApi> {
  api ??= new Promise((resolve) => {
    (window as unknown as { onSpotifyIframeApiReady: (loaded: IFrameApi) => void }).onSpotifyIframeApiReady = resolve;
    const script = document.createElement("script");
    script.src = SPOTIFY_IFRAME_API;
    script.async = true;
    document.body.appendChild(script);
  });
  return api;
}

/**
 * The artist's Spotify player through the iFrame API, so the record can play and pause it. It is
 * removed while the listing is not in view: the router keeps it mounted under a show page, playing.
 */
export function SpotifySample({ artistId, label, onPlaying, ref }: SampleProps) {
  const inView = useIsFocused();
  const host = useRef<HTMLDivElement>(null);
  const controller = useRef<Controller | null>(null);
  const report = useRef(onPlaying);
  useEffect(() => {
    report.current = onPlaying;
  }, [onPlaying]);

  useImperativeHandle(ref, () => ({ toggle: () => controller.current?.togglePlay() }), []);

  useEffect(() => {
    const parent = host.current;
    if (!inView || !parent) return;
    let gone = false;
    // The API replaces the element it gets: give it one React does not own.
    const element = document.createElement("div");
    parent.appendChild(element);
    void iframeApi().then((loaded) =>
      loaded.createController(element, { uri: spotifyArtistUri(artistId), width: "100%", height: PLAYER_HEIGHT }, (created) => {
        if (gone) return created.destroy();
        controller.current = created;
        created.addListener("playback_update", (event) => report.current(!event.data.isPaused));
      }),
    );
    return () => {
      gone = true;
      controller.current?.destroy();
      controller.current = null;
      parent.replaceChildren();
      report.current(false);
    };
  }, [artistId, inView]);

  return (
    <View style={styles.frame} accessibilityLabel={label}>
      <div ref={host} style={{ width: "100%", height: "100%" }} />
    </View>
  );
}
