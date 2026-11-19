import { StyleSheet } from "react-native";
import { colors, radius } from "../../../design/tokens";
import { MAP_HEIGHT } from "./VenueMap.constants";

export const styles = StyleSheet.create({
  frame: {
    height: MAP_HEIGHT,
    maxWidth: 640,
    borderRadius: radius.cardSmall,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.line,
    overflow: "hidden",
    // Google's own map ground, so the frame does not flash dark while it loads.
    backgroundColor: "#E9E5DC",
  },
  map: { flex: 1, backgroundColor: "transparent" },
});

/** The web iframe is a DOM element: it takes a CSS style, not a StyleSheet one. */
export const iframeStyle = { border: 0, width: "100%", height: "100%" } as const;
