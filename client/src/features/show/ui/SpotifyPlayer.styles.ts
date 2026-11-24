import { StyleSheet } from "react-native";
import { radius } from "../../../design/tokens";
import { PLAYER_HEIGHT } from "./SpotifyPlayer.constants";

export const styles = StyleSheet.create({
  // Spotify's embed draws its own rounded card; the frame only clips the corners to match.
  frame: { height: PLAYER_HEIGHT, borderRadius: radius.cardSmall, overflow: "hidden" },
  player: { flex: 1, backgroundColor: "transparent" },
});

/** The web iframe is a DOM element: it takes a CSS style, not a StyleSheet one. */
export const iframeStyle = { border: 0, width: "100%", height: "100%" } as const;
