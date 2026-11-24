import { StyleSheet } from "react-native";
import { radius } from "../../../../design/tokens";
import { PLAYER_HEIGHT } from "../../../show/ui/SpotifyPlayer.constants";

export const styles = StyleSheet.create({
  // Spotify's embed draws its own rounded card; the frame only clips the corners to match.
  frame: { height: PLAYER_HEIGHT, borderRadius: radius.cardSmall, overflow: "hidden" },
  player: { flex: 1, backgroundColor: "transparent" },
});
